from django.shortcuts import render

from django.contrib.auth.decorators import login_required
from AutoDocs.utils_group_required import group_required

@login_required
@group_required('admin', 'moodle')
def homepage(request):
    return render(request, 'caplogy_app/homepage.html')
