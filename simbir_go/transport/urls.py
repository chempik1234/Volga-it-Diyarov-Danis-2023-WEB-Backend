from django.urls import include, path

from .transport_controller_views import *
from .admin_transport_controller_views import *

app_name = 'authentication'
urlpatterns = [
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('Transport', TransportCreate.as_view()),
    path('Transport/<int:id>', TransportViewSetWithId.as_view({"get": "get", "put": "put", "delete": "delete"})),
    path('Admin/Transport', AdminTransportViewSetWithoutId.as_view({"get": "get", "post": "post"})),
    path('Admin/Transport/<int:id>', AdminTransportViewSetWithId.as_view({"get": "get", "put": "put",
                                                                          "delete": "delete"})),
]
