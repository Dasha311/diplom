from django.urls import path

from . import views

app_name = 'university'

urlpatterns = [
    path('', views.main_menu, name='main_menu'),
    path('schools/', views.schools_menu, name='schools_menu'),
    path('schools/digital-technologies/', views.school_of_digital, name='school_of_digital'),
    path('programs/information-systems/', views.info_systems_menu, name='info_systems_menu'),
]