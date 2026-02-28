from django.urls import path

from . import views

app_name = 'university'

urlpatterns = [
    path('', views.main_menu, name='main_menu'),
    path('schools/', views.schools_menu, name='schools_menu'),
    path('schools/management/', views.school_of_management, name='school_of_management'),
    path('schools/economics-and-finance/', views.school_of_economics, name='school_of_economics'),
    path('schools/politics-and-law/', views.school_of_politics, name='school_of_politics'),
    path('schools/media-and-cinema/', views.school_of_media, name='school_of_media'),
    path('schools/entrepreneurship/', views.school_of_business, name='school_of_business'),
    path('schools/hospitality-and-tourism/', views.school_of_tourism, name='school_of_tourism'),
    path('schools/health-sciences/', views.sharmanov_school, name='sharmanov_school'),
    path('schools/transformative-humanities/', views.school_of_transformative, name='school_of_transformative'),
    path('schools/digital-technologies/', views.school_of_digital, name='school_of_digital'),
    path('programs/information-systems/', views.info_systems_menu, name='info_systems_menu'),
]