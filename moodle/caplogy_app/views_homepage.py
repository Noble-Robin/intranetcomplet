from django.shortcuts import render

from AutoDocs.utils_group_required import group_required

@login_required
@group_required('admin', 'moodle')
def homepage(request):
    return render(request, 'caplogy_app/homepage.html')
