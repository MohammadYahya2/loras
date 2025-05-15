"""
URL configuration for loras project.

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
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

# Update Django auth settings
settings.LOGIN_URL = '/login/'
settings.LOGIN_REDIRECT_URL = '/'
settings.LOGOUT_REDIRECT_URL = '/'

urlpatterns = [
    path('admin/', admin.site.urls),
    # Redirect the default Django login URL to your custom login URL
    path('accounts/login/', RedirectView.as_view(url='/login/', query_string=True), name='account_login_redirect'),
    # Include the boutiqe URLs
    path('', include(('boutiqe.urls', 'boutiqe'), namespace='boutiqe')),
]

# Always add these lines for media and static files, regardless of DEBUG setting
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
