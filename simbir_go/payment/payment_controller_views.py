from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from authentication.models import User
import json
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""

from authentication.serializers import UserSerializer


class Hesoyam(generics.CreateAPIView):
    """
    Test payment API View (no permissions)\n
    POST /api/Payment/Hesoyam/{accountId} - increases user's balance by 250 000 (only admins can do it to other users!)
    """
    allowed_methods = ["POST"]
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer
    queryset = User.objects.all()

    @swagger_auto_schema(tags=['Payment controller'],
                         # manual_parameters=[openapi.Parameter('accountId', in_=openapi.IN_PATH, required=True,
                         #                                      type=openapi.TYPE_INTEGER)],
                         request_body=no_body,
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def post(self, request, accountId):
        # post_ = request.POST commented because JSON is used
        current_user = request.user
        if not current_user.is_staff and accountId != current_user.id:
            return Response({"detail": "Only admins can affect other users, and you're not one of them."},
                            status=status.HTTP_403_FORBIDDEN)
        user = get_object_or_404(User, id=accountId)
        self.serializer_class.update(None, user, {"balance": user.balance + 250000})
        return Response({"detail": "Successful payment (balance was increased by 250 000)"}, status=status.HTTP_200_OK)