from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import json
import logging
import requests
import re
from pathlib import Path
from collections import OrderedDict


SUPPORTED_LANGUAGES = {'ru', 'kz', 'en'}
DEFAULT_LANGUAGE = 'ru'
OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'
KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent / 'info.txt'
MAX_KNOWLEDGE_SNIPPETS = 1
MAX_SNIPPET_CHARS = 300
ANSWER_CACHE_SIZE = 150
SMALL_TALKS = {'привет', 'здравствуйте', 'как дела', 'сәлем', 'hello'}
SMALL_TALK_RESPONSE = 'Привет! Я помогу тебе с поступлением в AlmaU.'
KAZAKH_CHARS_RE = re.compile(r'[әіңғүұқөһ]', re.IGNORECASE)
CYRILLIC_RE = re.compile(r'[а-яё]', re.IGNORECASE)
LATIN_RE = re.compile(r'[a-z]', re.IGNORECASE)

LANGUAGE_PROMPTS = {
    'ru': 'Отвечай только на русском языке, опираясь на базу знаний.',
    'kz': 'Тек қазақ тілінде жауап бер. Жауап базалық ақпаратқа сүйенсін.',
    'en': 'Answer only in English using the knowledge base facts.',
}

FALLBACK_RESPONSES = {
    'ru': 'Простите, я не могу ответить на этот вопрос, но с радостью помогу вам с любой информацией о поступлении.',
    'kz': 'Кешіріңіз, бұл сұраққа жауап бере алмаймын, бірақ оқуға түсу туралы кез келген ақпаратпен қуана көмектесемін.',
    'en': 'Sorry, I cant answer this question, but I ll gladly help you with any admission information.',
}

SMALL_TALK_RULES = {
    'ru': 'Если пользователь здоровается или спрашивает "как дела", ответь дружелюбно и кратко.',
    'kz': 'Егер пайдаланушы амандасса немесе көңіл-күйді сұраса, қысқа әрі жылы жауап бер.',
    'en': 'If the user greets you or asks how you are, respond briefly and warmly.',
}

KNOWLEDGE_TRANSLATION_RULE = (
    'База знаний приведена на русском. Если пользователь пишет на казахском или английском, '
    'переводи релевантные факты из базы знаний на язык пользователя без потери смысла.'
)

_KNOWLEDGE_BASE_TEXT = None
_KNOWLEDGE_SECTIONS = None
ANSWER_CACHE = OrderedDict()
logger = logging.getLogger(__name__)

def _normalize_for_cache(text):
    return re.sub(r'\s+', ' ', (text or '').strip().lower())


def _extract_keywords(text):
    return {
        token
        for token in re.findall(r"[\w-]+", (text or '').lower())
        if len(token) >= 3
    }


def _split_knowledge_sections(knowledge_base_text):
    sections = []
    current = []
    for line in knowledge_base_text.splitlines():
        if line.strip().startswith('### ') and current:
            section_text = '\n'.join(current).strip()
            if section_text:
                sections.append(section_text)
            current = [line]
        else:
            current.append(line)

    if current:
        section_text = '\n'.join(current).strip()
        if section_text:
            sections.append(section_text)

    return sections or [knowledge_base_text]


def _get_relevant_knowledge(knowledge_base_text, user_message, history):
    query_tokens = _extract_keywords(user_message)
    if history:
        recent_user_text = ' '.join(msg['content'] for msg in history if msg['role'] == 'user')
        query_tokens |= _extract_keywords(recent_user_text)

    if not query_tokens:
        return knowledge_base_text[:MAX_SNIPPET_CHARS]

    sections = _KNOWLEDGE_SECTIONS or [knowledge_base_text]
    scored_sections = []
    for section in sections:
        section_tokens = _extract_keywords(section)
        overlap = len(query_tokens & section_tokens)
        if overlap:
            scored_sections.append((overlap, section))

    if not scored_sections:
        return knowledge_base_text[:MAX_SNIPPET_CHARS]

    scored_sections.sort(key=lambda item: item[0], reverse=True)
    top_sections = [section for _, section in scored_sections[:MAX_KNOWLEDGE_SNIPPETS]]
    return '\n\n'.join(top_sections)[:MAX_SNIPPET_CHARS]


def _cache_get(key):
    answer = ANSWER_CACHE.get(key)
    if answer is not None:
        ANSWER_CACHE.move_to_end(key)
    return answer


def _cache_set(key, value):
    ANSWER_CACHE[key] = value
    ANSWER_CACHE.move_to_end(key)
    while len(ANSWER_CACHE) > ANSWER_CACHE_SIZE:
        ANSWER_CACHE.popitem(last=False)

def ask_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            'model': 'mistral:latest',
            'prompt': prompt,
            'stream': False,
            'options': {
                'num_predict': 80,
                'temperature': 0.1,
                'top_p':0.7
            },
        },
        timeout=60,
    )

    response.raise_for_status()
    return response.json().get('response', '').strip()


def load_knowledge_base():
    global _KNOWLEDGE_BASE_TEXT, _KNOWLEDGE_SECTIONS
    if _KNOWLEDGE_BASE_TEXT is None:
        _KNOWLEDGE_BASE_TEXT = KNOWLEDGE_BASE_PATH.read_text(encoding='utf-8').strip()
        _KNOWLEDGE_SECTIONS = _split_knowledge_sections(_KNOWLEDGE_BASE_TEXT)
    return _KNOWLEDGE_BASE_TEXT


def detect_language(message):
    text = (message or '').strip().lower()
    if not text:
        return DEFAULT_LANGUAGE
    if KAZAKH_CHARS_RE.search(text):
        return 'kz'

    cyrillic_count = len(CYRILLIC_RE.findall(text))
    latin_count = len(LATIN_RE.findall(text))
    if latin_count > cyrillic_count:
        return 'en'
    if cyrillic_count > 0:
        return 'ru'
    return DEFAULT_LANGUAGE


def build_prompt(knowledge_base, user_message, language_code):
    knowledge_base = knowledge_base[:200]  # 🔥 ЖЁСТКИЙ ЛИМИТ

    return f"""
Ты AI-помощник AlmaU.
Отвечай кратко.

Язык: {language_code}

Контекст:
{knowledge_base}

Вопрос:
{user_message}

Ответ:
"""

def simple_search_kb(kb, question):
    q_words = set(question.lower().split())
    parts = kb.split("\n\n")

    best = ""
    best_score = 0

    for p in parts:
        score = sum(1 for w in q_words if w in p.lower())

        if score > best_score:
            best_score = score
            best = p

    return best[:300]   # 🔥 ТОЛЬКО ОДИН САМЫЙ ЛУЧШИЙ БЛОК

def get_current_language(request):
    lang = request.session.get('site_language', DEFAULT_LANGUAGE)
    return lang if lang in SUPPORTED_LANGUAGES else DEFAULT_LANGUAGE


def render_page(request, template_name):
    return render(request, template_name, {
        'current_language': get_current_language(request),
    })


def main_menu(request):
    return render_page(request, 'MainMenu.html')


def schools_menu(request):
    return render_page(request, 'SchoolsMenu.html')


def school_of_digital(request):
    return render_page(request, 'SchoolOfDigitalMenus.html')


def school_of_management(request):
    return render_page(request, 'SchoolOfManagement.html')


def school_of_economics(request):
    return render_page(request, 'SchoolOfEconomics.html')


def school_of_politics(request):
    return render_page(request, 'SchoolOfPolitics.html')


def school_of_media(request):
    return render_page(request, 'SchoolOfMedia.html')


def school_of_business(request):
    return render_page(request, 'SchoolOfBusiness.html')


def school_of_tourism(request):
    return render_page(request, 'SchoolOfTourism.html')


def sharmanov_school(request):
    return render_page(request, 'SharmanovSchool.html')


def school_of_transformative(request):
    return render_page(request, 'SchoolOfTransformative.html')


def info_systems_menu(request):
    return render_page(request, 'InfoSystemsMenu.html')


def chatbot_menu(request):
    return render_page(request, 'ChatBotMenu.html')


def apply_page(request):
    return render_page(request, 'ApplicationForm.html')


def set_language(request, lang_code):
    lang = (lang_code or '').lower()
    if lang not in SUPPORTED_LANGUAGES:
        return JsonResponse({'ok': False, 'error': 'unsupported_language'}, status=400)

    request.session['site_language'] = lang
    request.session.modified = True

    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('university:main_menu')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'ok': True, 'language': lang})
    return redirect(next_url)


@csrf_exempt
def chat(request):
    if request.method != 'POST':
        return JsonResponse({'answer': 'Метод не поддерживается.'}, status=405)
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        if not user_message:
            return JsonResponse({'answer': 'Введите сообщение.'}, status=400)
        if user_message.lower() in SMALL_TALKS:
            return JsonResponse({'answer': SMALL_TALK_RESPONSE})

        language_code = detect_language(user_message)
        knowledge_base = load_knowledge_base()
        relevant_knowledge = simple_search_kb(knowledge_base, user_message)
        prompt = build_prompt(relevant_knowledge, user_message, language_code)

        cache_key = f"{language_code}:{_normalize_for_cache(user_message)}"
        cached_answer = _cache_get(cache_key)
        answer = cached_answer or ask_ollama(prompt)
        if cached_answer is None:
            _cache_set(cache_key, answer)

        return JsonResponse({'answer': answer})        
    except json.JSONDecodeError:
        return JsonResponse({'answer': 'Некорректный JSON в запросе.'}, status=400)
    except requests.exceptions.Timeout:
        return JsonResponse({'answer': 'Ответ занял слишком много времени. Попробуйте еще раз чуть позже.'}, status=504)
    except requests.exceptions.RequestException:
        return JsonResponse({'answer': 'Сервис ответа временно недоступен. Попробуйте еще раз через минуту.'}, status=503)
    except Exception:
        logger.exception('Unexpected error in chat endpoint')
        return JsonResponse({'answer': 'Произошла непредвиденная ошибка. Попробуйте снова.'}, status=500)