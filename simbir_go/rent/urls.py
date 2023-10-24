from django.urls import include, path, re_path
from rest_framework import routers

from .rent_controller_views import *
from .admin_rent_controller_views import *

# router = routers.DefaultRouter()
# router.register(r'Account/Me', Me, basename="authentication")  # .as_view({'get': 'get'}), basename="Me"
# router.register(r'Account/SignIn', SignIn, basename="authentication")
# router.register(r'Account/SignUp', SignUp, basename="authentication")
# router.register(r'Account/SignOut', SignOut, basename="authentication")
# router.register(r'Account/Update', Update, basename="authentication")
# router.register(r'Admin/Account/<int:id>', AdminViewSetWithId, basename="authentication")
# router.register(r'Admin/Account', AdminViewSet, basename="authentication")

app_name = 'rent'
urlpatterns = [
    # path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    path('Rent/Transport/', GetAvailableTransport.as_view()),
    path('Rent/<int:rentId>', GetRent.as_view()),
    path('Rent/MyHistory', MyHistory.as_view()),
    path('Rent/TransportHistory/<int:transportId>', TransportHistory.as_view()),
    path('Rent/New/<int:transportId>', NewRent.as_view()),
    path('Rent/End/<int:rentId>', EndRent.as_view()),
    # Admins
    path('Admin/Rent/<int:rentId>', AdminRentViewSetWithId.as_view({'get': 'get', 'put': 'put',
                                                                    'delete': 'delete'})),
    # path('Admin/Rent/<int:id>', AdminRentViewPut.as_view()),
    path('Admin/Rent/UserHistory/<int:userId>', AdminUserHistory.as_view()),
    path('Admin/Rent/TransportHistory/<int:transportId>', AdminTransportHistory.as_view()),
    path('Admin/Rent', AdminNewRent.as_view()),
    path('Admin/Rent/End/<int:rentId>', AdminEndRent.as_view()),

]
# print(*router.urls, sep='\n')
