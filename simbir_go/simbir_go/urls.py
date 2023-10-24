"""
URL configuration for simbir_go project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions

schema_view = get_schema_view(
    openapi.Info(
        title="Simbir.GO API",
        default_version='v1',
        description="### ОГРОМНОЕ СПАСИБО за то,\n 1) что заставили искать хостинги для ТЕСТОВОЙ базы данных, ещё и на "
                    "PostgreSQL, а потом подтвержать паспортные данные, чтобы настраивать его! Вот то, что называется "
                    "'чёткие требования заказчика'.\n 2) Не смущайтесь, пожалуйста, что вся авто-документация на "
                    "английском, я просто привык на нём писать, потому что это всё-таки стандарт."
                    "# Авторизация - кнопка Authorize, перед токеном добавьте префикс 'Token'.",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="dandijar@yandex.ru"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path('admin/', admin.site.urls),
    # Swagger
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    # API's
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('authentication.urls', namespace='authentication')),
    path('api/', include('payment.urls', namespace='payment')),
    path('api/', include('transport.urls', namespace='transport')),
    path('api/', include('rent.urls', namespace='rent'))
    # path('api/', include('rent.urls', namespace='rent'))
]
