from django.test import TestCase
from django.urls import reverse

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
