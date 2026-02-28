from django.shortcuts import render

def main_menu(request):
    return render(request, 'MainMenu.html')


def schools_menu(request):
    return render(request, 'SchoolsMenu.html')


def school_of_digital(request):
    return render(request, 'SchoolOfDigitalMenus.html')

def school_of_management(request):
    return render(request, 'SchoolOfManagement.html')


def school_of_economics(request):
    return render(request, 'SchoolOfEconomics.html')


def school_of_politics(request):
    return render(request, 'SchoolOfPolitics.html')


def school_of_media(request):
    return render(request, 'SchoolOfMedia.html')


def school_of_business(request):
    return render(request, 'SchoolOfBusiness.html')


def school_of_tourism(request):
    return render(request, 'SchoolOfTourism.html')


def sharmanov_school(request):
    return render(request, 'SharmanovSchool.html')


def school_of_transformative(request):
    return render(request, 'School ofTransformative.html')


def info_systems_menu(request):
    return render(request, 'InfoSystemsMenu.html')
