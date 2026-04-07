from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import json
import requests

SUPPORTED_LANGUAGES = {'ru', 'kz', 'en'}
DEFAULT_LANGUAGE = 'ru'
OLLAMA_URL = 'http://127.0.0.1:11434/api/generate'
MAX_TURNS = 10

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


def build_prompt(history, user_message):
    lines = ['Отвечай на том же языке, что и последнее сообщение пользователя.']

    for turn in history[-MAX_TURNS:]:
        lines.append(f"Пользователь: {turn['user']}")
        lines.append(f"ИИ: {turn['assistant']}")

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

    history = request.session.get('chat_history', [])
    if not isinstance(history, list):
        history = []

    prompt = build_prompt(history, user_message)

    try:
        answer = ask_ollama(prompt)
    except requests.exceptions.RequestException:
        return JsonResponse({'answer': 'Сервис ответа временно недоступен. Попробуйте еще раз через минуту.'}, status=503)

    history.append({'user': user_message, 'assistant': answer})
    request.session['chat_history'] = history[-MAX_TURNS:]
    request.session.modified = True

    return JsonResponse({'answer': answer})