

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from caplogy_app.views import login_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
    path('', include('homepage.urls')),
    path('moodle/', include('caplogy_app.urls')),
    path('autodocs/', include('AutoDocs.myproject.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
