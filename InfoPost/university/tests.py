from django.test import TestCase
from django.urls import reverse
from unittest.mock import Mock, patch


class UniversityRoutesTests(TestCase):
    def test_pages_are_available(self):
        route_names = [
            'university:main_menu',
            'university:schools_menu',
            'university:school_of_management',
            'university:school_of_economics',
            'university:school_of_politics',
            'university:school_of_media',
            'university:school_of_business',
            'university:school_of_tourism',
            'university:sharmanov_school',
            'university:school_of_transformative',
            'university:school_of_digital',
            'university:info_systems_menu',
            'university:chatbot_menu',
        ]

        for route_name in route_names:
            with self.subTest(route_name=route_name):
                response = self.client.get(reverse(route_name))

                self.assertEqual(response.status_code, 200)

    def test_main_page_uses_absolute_static_urls(self):
        response = self.client.get(reverse('university:main_menu'))

        self.assertContains(response, '/static/png/AlmaU.png')
        self.assertNotContains(response, 'img/hori.jpg')

    @patch('university.views.requests.post')
    def test_chat_api_returns_answer_from_model(self, mock_post):
        mock_response = Mock()
        mock_response.json.return_value = {'response': 'Тестовый ответ'}
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response

        response = self.client.post(
            reverse('university:chat_api'),
            data='{"message":"как поступить?"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {'answer': 'Тестовый ответ'})

        payload = mock_post.call_args.kwargs['json']
        prompt = payload['prompt']
        self.assertIn('Ты помощник AlmaU.', prompt)
        self.assertEqual(payload['options']['num_predict'], 80)
        self.assertEqual(payload['options']['temperature'], 0.2)

    @patch('university.views.requests.post')
    def test_chat_api_returns_fast_small_talk_response_without_model(self, mock_post):
        response = self.client.post(
            reverse('university:chat_api'),
            data='{"message":"привет"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(
            response.content,
            {'answer': 'Привет! Я помогу тебе с поступлением в AlmaU.'},
        )
        mock_post.assert_not_called()        

    @patch('university.views.load_knowledge_base', side_effect=RuntimeError('broken knowledge base'))
    def test_chat_api_returns_json_on_unexpected_error(self, _):
        response = self.client.post(
            reverse('university:chat_api'),
            data='{"message":"Расскажите про гранты"}',
            content_type='application/json',
        )

        self.assertEqual(response.status_code, 500)
        self.assertJSONEqual(
            response.content,
            {'answer': 'Произошла непредвиденная ошибка. Попробуйте снова.'},
        )