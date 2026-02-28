from django.shortcuts import render

def main_menu(request):
    return render(request, 'MainMenu.html')


def schools_menu(request):
    return render(request, 'SchoolsMenu.html')


def school_of_digital(request):
    return render(request, 'SchoolOfDigitalMenus.html')


def info_systems_menu(request):
    return render(request, 'InfoSystemsMenu.html')
