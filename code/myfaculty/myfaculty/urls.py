"""
URL configuration for myfaculty project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from core.views import media_download
from myprofile.legal import LegalPage


urlpatterns = [
    path("i18n/", include("django.conf.urls.i18n")),
    path('media/<path:path>', media_download, name='media_download'),
    # Deliberately outside i18n_patterns (unlike the old api/, which is
    # locale-prefixed) - apiv2 is a REST API, not a locale-aware UI.
    path('apiv2/', include('apiv2.urls')),
    # Public legal pages (also given to Google's OAuth consent screen)
    path('privacy/', LegalPage.as_view(template_name='legal/privacy.html'), name='privacy'),
    path('terms/', LegalPage.as_view(template_name='legal/terms.html'), name='terms'),
    # Google sign-in (not allauth.urls, which would shadow django.contrib.auth.urls).
    # Outside i18n_patterns so the OAuth redirect URI is fixed:
    # https://<host>/accounts/google/login/callback/
    path("accounts/", include("allauth.socialaccount.providers.google.urls")),
    path("accounts/", include("allauth.socialaccount.urls")),
]

urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path("", include("myprofile.urls")),  
    path('associates/', include('associates.urls')),  
    path('projects/', include('projects.urls')),
    path('timesheets/', include('timesheets.urls')),  
    path('theses/', include('theses.urls')),      
    path('leaves/', include('leaves.urls')),
    path('curricula/', include('curricula.urls')),  
    path('phdstuds/', include('phdstuds.urls')),
    path('hrms/',include('hrms.urls')),
    path('phdapplications/', include('phdapplications.urls')),  
    path("accounts/", include("django.contrib.auth.urls")) ,
)


if settings.DEBUG: 
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
