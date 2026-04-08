from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import json
import requests
import re
from pathlib import Path


SUPPORTED_LANGUAGES = {'ru', 'kz', 'en'}
DEFAULT_LANGUAGE = 'ru'
OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'
MAX_HISTORY_MESSAGES = 10
KNOWLEDGE_BASE_PATH = Path(__file__).resolve().parent / 'info.txt'
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

def ask_ollama(prompt):
    response = requests.post(
        OLLAMA_URL,
        json={
            'model': 'phi3',
            'prompt': prompt,
            'stream': False,
        },
        timeout=30,
    )
    response.raise_for_status()
    return response.json().get('response', '').strip()


def load_knowledge_base():
    global _KNOWLEDGE_BASE_TEXT
    if _KNOWLEDGE_BASE_TEXT is None:
        _KNOWLEDGE_BASE_TEXT = KNOWLEDGE_BASE_PATH.read_text(encoding='utf-8').strip()
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


def normalize_history(raw_history):
    if not isinstance(raw_history, list):
        return []

    normalized = []
    for item in raw_history:
        if isinstance(item, dict) and 'role' in item and 'content' in item:
            role = item.get('role')
            content = (item.get('content') or '').strip()
            if role in {'user', 'assistant'} and content:
                normalized.append({'role': role, 'content': content})
        elif isinstance(item, dict) and 'user' in item and 'assistant' in item:
            user_content = (item.get('user') or '').strip()
            assistant_content = (item.get('assistant') or '').strip()
            if user_content:
                normalized.append({'role': 'user', 'content': user_content})
            if assistant_content:
                normalized.append({'role': 'assistant', 'content': assistant_content})
    return normalized[-MAX_HISTORY_MESSAGES:]


def build_prompt(knowledge_base, history, user_message, language_code):
    fallback_message = FALLBACK_RESPONSES.get(language_code, FALLBACK_RESPONSES[DEFAULT_LANGUAGE])
    small_talk_rule = SMALL_TALK_RULES.get(language_code, SMALL_TALK_RULES[DEFAULT_LANGUAGE])

    lines = [
        '[Информация из базы знаний]',
        knowledge_base,
        '',
        KNOWLEDGE_TRANSLATION_RULE,
        LANGUAGE_PROMPTS.get(language_code, LANGUAGE_PROMPTS[DEFAULT_LANGUAGE]),
        small_talk_rule,
        (
            'Если точного ответа нет в базе знаний или вопрос не относится к поступлению, программам, '
            f'контактам и учебному процессу, ответь только этой фразой: "{fallback_message}"'
        ),
        'Отвечай кратко, точно и по делу.',
    ]

    for message in history[-MAX_HISTORY_MESSAGES:]:
        speaker = 'Пользователь' if message['role'] == 'user' else 'ИИ'
        lines.append(f"{speaker}: {message['content']}")

    lines.append(f'Пользователь: {user_message}')
    lines.append('ИИ:')
    return '\n'.join(lines)


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
    except json.JSONDecodeError:
        return JsonResponse({'answer': 'Некорректный JSON в запросе.'}, status=400)

    user_message = data.get('message', '').strip()
    if not user_message:
        return JsonResponse({'answer': 'Введите сообщение.'}, status=400)

    language_code = detect_language(user_message)
    history = normalize_history(request.session.get('chat_history', []))
    knowledge_base = load_knowledge_base()
    prompt = build_prompt(knowledge_base, history, user_message, language_code)

    try:
        answer = ask_ollama(prompt)
    except requests.exceptions.Timeout:
        return JsonResponse({'answer': 'Ответ занял слишком много времени. Попробуйте еще раз чуть позже.'}, status=504)        
    except requests.exceptions.RequestException:
        return JsonResponse({'answer': 'Сервис ответа временно недоступен. Попробуйте еще раз через минуту.'}, status=503)
    except Exception:
        return JsonResponse({'answer': 'Произошла непредвиденная ошибка. Попробуйте снова.'}, status=500)

    history.append({'role': 'user', 'content': user_message})
    history.append({'role': 'assistant', 'content': answer})
    request.session['chat_history'] = history[-MAX_HISTORY_MESSAGES:]
    request.session['chat_language'] = language_code
    request.session.modified = True

    return JsonResponse({'answer': answer})