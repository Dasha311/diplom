from pathlib import Path
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

import requests
import json
import os

SUPPORTED_LANGUAGES = {'ru', 'kz', 'en'}
DEFAULT_LANGUAGE = 'ru'
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "phi3")
DATA_FILE = Path(__file__).resolve().parents[2] / "data.txt"



def _build_ollama_endpoints():
    base = OLLAMA_BASE_URL.rstrip("/")
    normalized_base = base.removesuffix("/v1").removesuffix("/api")
    endpoints = [
        f"{normalized_base}/api/generate",
        f"{normalized_base}/api/chat",
        f"{normalized_base}/v1/chat/completions",
    ]
    return list(dict.fromkeys(endpoints))


def ask_ollama(prompt):
    endpoints = _build_ollama_endpoints()

    last_error = None
    for endpoint in endpoints:
        try:
            if endpoint.endswith("/api/generate"):
                payload = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
            elif endpoint.endswith("/api/chat"):
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                }
            else:
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": [{"role": "user", "content": prompt}],
                    "stream": False,
                }

            response = requests.post(endpoint, json=payload, timeout=60)

            if response.status_code == 404:
                details = ""
                try:
                    details = response.json().get("error", "")
                except ValueError:
                    details = response.text.strip()
                details = f" ({details})" if details else ""
                last_error = f"{endpoint} вернул 404{details}"
                continue

            response.raise_for_status()
            data = response.json()

            if endpoint.endswith("/api/generate"):
                return data.get("response", "Ошибка ответа от ИИ")

            if endpoint.endswith("/api/chat"):
                return (data.get("message") or {}).get("content", "Ошибка ответа от ИИ")

            choices = data.get("choices", [])
            if choices:
                return (choices[0].get("message") or {}).get("content", "Ошибка ответа от ИИ")
            return "Ошибка ответа от ИИ"

        except requests.RequestException as exc:
            last_error = str(exc)
            continue

    raise RuntimeError(
        "Не удалось подключиться к ИИ. Проверьте OLLAMA_BASE_URL и доступность сервера. "
        f"Последняя ошибка: {last_error}"
    )


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


# =========================
# 🤖 ВОТ ТВОЙ ИИ БОТ
# =========================
@csrf_exempt
def chat(request):
    try:
        if request.method != "POST":
            return JsonResponse({"answer": "Метод не поддерживается"}, status=405)
        data = json.loads(request.body)
        user_message = data.get("message", "").strip()
        if not user_message:
            return JsonResponse({"answer": "Введите сообщение"}, status=400)

        # читаем файл с данными
        with open(DATA_FILE, encoding="utf-8") as f:
            context = f.read()

        prompt = f"""
Ты помощник абитуриента университета.
Отвечай на русском, казахском или английском.
Отвечай КОРОТКО и по делу.
Отвечай на том же языке, что и вопрос.
Если нет информации — скажи "Не найдено".

Информация:
{context}

Вопрос:
{user_message}
"""
        answer = ask_ollama(prompt)

        return JsonResponse({"answer": answer})

    except Exception as e:
        return JsonResponse({"answer": f"Ошибка: {str(e)}"})