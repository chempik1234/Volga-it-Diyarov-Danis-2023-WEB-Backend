from django.urls import include, path
from rest_framework import routers

from .account_controller_views import *
from .admin_account_controller import *

# router = routers.DefaultRouter()
# router.register(r'Account/Me', Me, basename="authentication")  # .as_view({'get': 'get'}), basename="Me"
# router.register(r'Account/SignIn', SignIn, basename="authentication")
# router.register(r'Account/SignUp', SignUp, basename="authentication")
# router.register(r'Account/SignOut', SignOut, basename="authentication")
# router.register(r'Account/Update', Update, basename="authentication")
# router.register(r'Admin/Account/<int:id>', AdminViewSetWithId, basename="authentication")
# router.register(r'Admin/Account', AdminViewSet, basename="authentication")

app_name = 'authentication'
urlpatterns = [
    # path('', include(router.urls)),
    # path('api-auth/', include('rest_framework.urls', namespace='rest_framework'))
    path('Account/Me', Me.as_view()),
    path('Account/SignIn', SignIn.as_view()),
    path('Account/SignUp', SignUp.as_view()),
    path('Account/SignOut', SignOut.as_view()),
    path('Account/Update', Update.as_view()),
    path('Admin/Account/<int:id>', AdminAccountsViewSetWithId.as_view({'get': 'get', 'put': 'put', 'delete': 'delete'})),
    path('Admin/Account/', AdminAccountsViewSet.as_view({'get': 'get', 'post': 'post'}))
]
# print(*router.urls, sep='\n')
