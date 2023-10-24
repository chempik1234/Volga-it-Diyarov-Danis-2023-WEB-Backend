from django.urls import include, path
from rest_framework import routers

from .payment_controller_views import *

app_name = 'payment'
urlpatterns = [
    # path('', include(router.urls)),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('Payment/Hesoyam/<int:accountId>', Hesoyam.as_view()),
]