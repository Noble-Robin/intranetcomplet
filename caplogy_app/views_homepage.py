from django.shortcuts import render

def homepage(request):
    return render(request, 'caplogy_app/homepage.html')
