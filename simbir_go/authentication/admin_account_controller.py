from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.viewsets import ViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import User
import json
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""


from .serializers import UserSerializer


class AdminAccountsViewSet(ViewSet):
    """
    API ViewSet, /api/Admin/Account/ permissions = (IsAdminUser,);\n
    GET /api/Admin/Account - List of 'count' Users with id's counting from start (params: start, end: int);\n
    POST /api/Admin/Account - Creates a new user (body required).
    """
    allowed_methods = ["GET", "POST"]
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(manual_parameters=[openapi.Parameter('start', in_=openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                                                              required=True),
                                            openapi.Parameter('count', in_=openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                                                              required=True)],
                         tags=['Admin account controller'],
                         responses={
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),})
    def get(self, request):
        query = request.GET
        start, count = query.get('start'), query.get('count')
        errors = ""
        if start is None:
            errors += "Parameter named 'start' (of int) is required. "
        elif not start.isdigit():
            errors += "Parameter named 'start' must be an int. "
        elif int(start) < 0:
            errors += "Parameter named 'start' must be >= 0. "

        if count is None:
            errors += "Parameter named 'count' (of int) is required. "
        elif not count.isdigit():
            errors += "Parameter named 'count' must be an int ."
        elif int(count) < 0:
            errors += "Parameter named 'count' must be >= 0. "

        if errors:
            return Response({"detail": "Bad request: " + errors}, status=status.HTTP_400_BAD_REQUEST)

        queryset = self.queryset.filter(id__gte=int(start), id__lt=int(start) + int(count))
        serialized = self.serializer_class(queryset, many=True)  # Many=True is used because a list is needed
        return Response(serialized.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Admin account controller'],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             required=["username", "password", "isAdmin", "balance"],
                             properties={
                                 "username": openapi.Schema('username', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 "password": openapi.Schema('password', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 "isAdmin": openapi.Schema('isAdmin', in_=openapi.IN_BODY, type=openapi.TYPE_BOOLEAN),
                                 "balance": openapi.Schema('balance', in_=openapi.IN_BODY, type=openapi.TYPE_NUMBER),
                             }
                         ),
                         responses={
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),})
    def post(self, request):
        try:  # json body needs to be decoded, but if it contains syntax errors, an exception occures
            body_unicode = request.body.decode('utf-8')
            post_ = json.loads(body_unicode)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        # post_ = request.POST
        username, password, is_admin, balance = post_.get("username"), post_.get("password"), post_.get("isAdmin"), \
                                                post_.get("balance")
        if not username or not password or not isinstance(is_admin, bool) or\
                (not isinstance(balance, float) and not isinstance(balance, int)):
            return Response({"detail": "Required body content: username (str), password (str), isAdmin (bool), "
                                       "balance (float)"},
                            status=status.HTTP_400_BAD_REQUEST)
        elif self.queryset.filter(username=username):
            return Response({"detail": "User with given username already exists."}, status=status.HTTP_400_BAD_REQUEST)
        # user = User(username=username, balance=balance, is_staff=is_admin)
        # user.set_password(password)
        try:
            user = self.serializer_class.create(self.serializer_class(), {"username": username,
                                                                          "password": password,
                                                                          "is_staff": is_admin,
                                                                          "balance": balance})
        except Exception as e:
            return Response(str(e), status=status.HTTP_400_BAD_REQUEST)
        serialized = self.serializer_class(user)
        # if not serialized.is_valid():
        #     return Response({"detail":serialized.errors}, status=status.HTTP_400_BAD_REQUEST)
        response = Response(serialized.data, status=status.HTTP_201_CREATED)
        login(request, authenticate(request, username=username, password=password))
        return response


class AdminAccountsViewSetWithId(ViewSet):
    """
    API ViewSet, /api/Admin/Account/{id} permissions = (IsAdminUser,);\n
    GET /api/Admin/Account/{id} - Fields of user with given id;\n
    PUT /api/Admin/Account/{id} - User Partial Update;\n
    DELETE /api/Admin/Account/{id} - Make User with given id inactive (is_active = False).
    """
    permission_classes = (IsAdminUser,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(tags=['Admin account controller'],
                         responses={
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT)})
    def get(self, request, id):
        return Response(self.serializer_class(get_object_or_404(User, id=id)).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Admin account controller'],
                         # manual_parameters=[openapi.Parameter('id')],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             #  required=["username", "password", "isAdmin", "balance"],
                             properties={
                                 "username": openapi.Schema('username', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 "password": openapi.Schema('password', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 "isAdmin": openapi.Schema('isAdmin', in_=openapi.IN_BODY, type=openapi.TYPE_BOOLEAN),
                                 "balance": openapi.Schema('balance', in_=openapi.IN_BODY, type=openapi.TYPE_NUMBER),
                             }
                         ),
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT)
                         })
    def put(self, request, id):
        user = get_object_or_404(User, id=id)
        put_ = request.data
        username, password, is_admin, balance = put_.get("username"), put_.get("password"), put_.get('isAdmin'), \
                                                put_.get('balance')
        if User.objects.filter(username=username).exclude(id=id).exists():
            return Response({"detail": "User with given username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        changes_data = {}  # dict with all changes that are not None
        if username is not None:
            changes_data["username"] = username
        if password is not None:
            user.set_password(password)
        if is_admin is not None:
            changes_data["is_staff"] = True
        if balance is not None:
            changes_data["balance"] = balance

        self.serializer_class.update(self.serializer_class(), user, changes_data)
        return Response({"detail": "Updated fields successfully"}, status=status.HTTP_202_ACCEPTED)

    @swagger_auto_schema(tags=['Admin account controller'],
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)},),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT)})
    def delete(self, request, id):
        user = get_object_or_404(User, id=id)
        user.is_active = False
        return Response({'detail': 'Successfully deleted (made inactive) account with given id.'},
                        status=status.HTTP_200_OK)
