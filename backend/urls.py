"""
URL configuration for backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django_cas_ng import views as cas_views
from class_catch_app.views import cas_callback_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('class_catch_app.urls')),
    # cas
    path("cas/login/", cas_views.LoginView.as_view(), name="cas_login"),
    path("cas/logout/", cas_views.LogoutView.as_view(), name="cas_logout"),
    path("cas/callback/", cas_callback_view, name="cas_callback"),
]
