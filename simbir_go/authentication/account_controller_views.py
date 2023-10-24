from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
# from rest_framework.viewsets import ModelViewSet, ViewSet, GenericViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import User
import json
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""

from .serializers import UserSerializer


class Me(generics.GenericAPIView):
    """
    Shows the fields of user's current account. permissions = (IsAuthenticated).\n
    GET /api/Account/Me - gets information about current user's fields
    """
    allowed_methods = ["GET"]
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    # @classmethod
    # def get_extra_actions(cls):
    #     return []
#
    def get_queryset(self):
        user = self.request.user
        return user  # .account.all()

    def get_object(self):
        obj = self.get_queryset()
        self.check_object_permissions(self.request, obj)
        return obj

    @swagger_auto_schema(tags=['Account controller'],
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                         })
    def get(self, request):  # {"token": self.get_object().token}
        return Response(self.serializer_class(request.user).data, status=status.HTTP_200_OK)


class SignIn(generics.GenericAPIView):
    """
    Recreating a JWT for given User Api View (no permissions,)\n
    POST /api/Account/SignIn - returns user's JWT (!) username and password must be present in the request body (!)
    """
    allowed_methods = ["POST"]
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(tags=['Account controller'],
                         request_body=openapi.Schema(
                             required=['username', 'password'],
                             type=openapi.TYPE_OBJECT,
                             properties={
                                 'username': openapi.Schema('username', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 'password': openapi.Schema('password', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                             }),
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT, properties={
                                 'token': openapi.Schema('token', description="Auth token without the prefix "
                                                                              "(THE PREFIX IS 'Token'!!! The prefix is"
                                                                              "required to authenticate manually!!!!!)",
                                                         type=openapi.TYPE_STRING)
                             }),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def post(self, request):
        # post_ = request.POST commented because JSON is used
        body_unicode = request.body.decode('utf-8')
        post_ = json.loads(body_unicode)
        username, password = post_.get("username"), post_.get("password")
        if not username or not password:
            return Response({"detail": "Username and password must be present and be non-empty strings."},
                            status=status.HTTP_400_BAD_REQUEST)
        object_ = get_object_or_404(User, username=username)
        if not object_.check_password(password):
            return Response({"detail": "Wrong password."}, status=status.HTTP_400_BAD_REQUEST)
        login(request, object_)
        return Response({"token": object_.token}, status=status.HTTP_200_OK)


class SignUp(generics.GenericAPIView):
    """
    Signing Up Api View (no permissions)\n
    POST /api/Account/SignUp - creates a new account (username, password are stated in the body)
    """
    allowed_methods = ["POST"]
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(tags=['Account controller'],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             required=['username', 'password'],
                             properties={
                                 'username': openapi.Schema('username', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 'password': openapi.Schema('password', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                             }),
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def post(self, request):
        # post_ = request.POST commented because JSON is used
        try:  # json body needs to be decoded, but if it contains syntax errors, an exception occures
            body_unicode = request.body.decode('utf-8')
            post_ = json.loads(body_unicode)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        username, password = post_.get("username"), post_.get("password")
        if not username or not password:
            return Response({"detail": "Bad response: both username and password are required and mustn't be empty"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif self.queryset.filter(username=username):
            return Response({"detail": "User with given username already exists."}, status=status.HTTP_400_BAD_REQUEST)
        response = self.create(request)
        login(request, authenticate(request, username=username, password=password))
        return response


class SignOut(generics.GenericAPIView):
    """
    Signing Out Api View (no permissions)\n
    POST /api/Account/SignOut - simply logs the current user out.
    """
    allowed_methods = ["POST"]
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(tags=['Account controller'],
                         request_body=no_body,
                         manual_parameters=[],
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                         })
    def post(self, request):
        logout(request)
        return Response({"detail": "Logged out successfully"}, status=status.HTTP_200_OK)


class Update(generics.GenericAPIView):
    """
    User Partial Update Api View (no permissions)\n
    PUT /api/Account/Update - updates current user's fields
    """
    allowed_methods = ["PUT"]
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(tags=['Account controller'],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             # required=['username', 'password'],
                             properties={
                                 'username': openapi.Schema('username', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 'password': openapi.Schema('password', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                             }),
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                         })
    def put(self, request):
        put_ = request.data
        username, password = put_.get("username"), put_.get("password")
        if User.objects.filter(username=username).exclude(id=request.user.id).exists():
            return Response({"detail": "User with given username already exists."}, status=status.HTTP_400_BAD_REQUEST)
        errors = ""
        if not isinstance(username, str) and username is not None:
            errors += "username must either be absent or be present as a non-empty string; "
        if not isinstance(password, str) and password is not None:
            errors += "password must either be absent or be present as a non-empty string; "
        user = request.user
        data = {}
        if username:
            data["username"] = username
        if password:
            data["password"] = password
        UserSerializer.update(self.serializer_class(), user, data)
        login(request, user)
        return Response({"detail": "Updated fields successfully"}, status=status.HTTP_200_OK)
