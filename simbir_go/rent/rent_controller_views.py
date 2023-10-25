from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.viewsets import ViewSet
from django.shortcuts import get_object_or_404
from django.db.models.expressions import F
from django.db.models import FloatField
from django.contrib.auth import authenticate, login, logout
from transport.models import Transport
from .models import Rent
from datetime import datetime
import json
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""

from transport.serializers import TransportSerializer
from .serializers import RentSerializer


class GetAvailableTransport(generics.GenericAPIView):
    """
    Get available transport; request: latitude, longitude, radius, type[Car, Bike, Scooter, Any] (AllowAny)\n
    GET /api/Rent/Transport
    """
    allowed_methods = ["GET"]
    permission_classes = (AllowAny,)
    serializer_class = TransportSerializer
    queryset = Transport.objects.all()

    @swagger_auto_schema(tags=['Rent controller'],
                         manual_parameters=
                         [openapi.Parameter('longitude', in_=openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
                          openapi.Parameter('latitude', in_=openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
                          openapi.Parameter('radius', in_=openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
                          openapi.Parameter('type', in_=openapi.IN_QUERY, type=openapi.TYPE_STRING,
                                            required=True)],
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def get(self, request):
        query = request.GET
        longitude, latitude, radius, transport_type = query.get('longitude'), query.get('latitude'),\
                                                      query.get('radius'), query.get('type')
        errors = ""

        try:
            longitude = float(longitude)
        except Exception:
            errors += "longitude must be present as a float; "
        try:
            latitude = float(latitude)
        except Exception:
            errors += "latitude must be present as a float; "
        try:
            radius = float(radius)
        except Exception:
            errors += "radius must be present as a float; "
        if transport_type not in Transport.CHOICE_TO_TRANSPORT.keys() and transport_type != "All":
            errors += "type must be present as one of these strings: 'Car', 'Bike', 'Scooter', 'All'"

        if errors:
            return Response("Bad request: " + errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.annotate(distance=(F('latitude')-latitude)*(F('latitude')-latitude)+
                                                   (F('longitude')-longitude)*(F('longitude')-longitude)).\
            filter(distance__lte=radius**2)
        # This query finds all the transport using piphagorus' theorema
        if transport_type != "All":
            queryset = queryset.filter(transport_type=Transport.CHOICE_TO_TRANSPORT[transport_type])
        serialized = self.serializer_class(queryset, many=True)  # Many=True is used because a list is needed
        return Response(serialized.data, status=status.HTTP_200_OK)


class GetRent(generics.GenericAPIView):
    """
    Get information about rent using it's id (only for transport owner and renter) (IsAuthenticated)\n
    GET /api/Rent/{rentId}
    """
    allowed_methods = ["GET"]
    permission_classes = (IsAuthenticated,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Rent controller'],
                         manual_parameters=
                         [openapi.Parameter('rentId', in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True)],
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def get(self, request, rentId):
        rent = get_object_or_404(Rent, id=rentId)
        if request.user != rent.transport_id.owner_id and request.user != rent.user_id:
            return Response({'detail': "Available only for transport owner and renter"},
                            status=status.HTTP_403_FORBIDDEN)
        serialized = self.serializer_class(rent)
        return Response(serialized.data, status=status.HTTP_200_OK)


class MyHistory(generics.GenericAPIView):
    """
    Get current user's rent history (IsAuthenticated)\n
    GET /api/Rent/MyHistory
    """
    allowed_methods = ["GET"]
    permission_classes = (IsAuthenticated,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Rent controller'],)
    def get(self, request):
        queryset = Rent.objects.filter(user_id=request.user)  # returns all rents made by current user
        serialized = self.serializer_class(queryset, many=True)  # Many=True is used because a list is needed
        return Response(serialized.data, status=status.HTTP_200_OK)


class TransportHistory(generics.GenericAPIView):
    """
    Get a transport's rent history, only for the transport owner (IsAuthenticated)\n
    GET /api/Rent/TransportHistory/{transportId}
    """
    allowed_methods = ["GET"]
    permission_classes = (IsAuthenticated,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Rent controller'],
                         manual_parameters=
                         [openapi.Parameter('transportId', in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER,
                                            required=True)],
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT)
                         })
    def get(self, request, transportId):
        transport = get_object_or_404(Transport, id=transportId)
        if request.user != transport.owner:
            return Response({'detail': "Only available for the transport owner."}, status=status.HTTP_403_FORBIDDEN)
        queryset = Rent.objects.filter(transport_id=transport)
        serialized = self.serializer_class(queryset, many=True)  # Many=True is used because a list is needed
        return Response(serialized.data, status=status.HTTP_200_OK)


class NewRent(generics.GenericAPIView):
    """
    Creates an active rent, NOT available for the transport owner; query: rentType [Minutes, Days]\n
    POST /api/Rent/New/{transportId}
    """
    allowed_methods = ["POST"]
    permission_classes = (IsAuthenticated,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Rent controller'],
                         manual_parameters=[openapi.Parameter('transportId', in_=openapi.IN_PATH,
                                                              type=openapi.TYPE_INTEGER, required=True),
                                            openapi.Parameter('rentType', in_=openapi.IN_QUERY,
                                                              type=openapi.TYPE_STRING, required=True)],
                         request_body=no_body,
                         responses={
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT),
                             500: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                         })
    def post(self, request, transportId):
        transport = get_object_or_404(Transport, id=transportId)
        if transport.owner == request.user:
            return Response({"detail": "Not available for transport owner."}, status=status.HTTP_403_FORBIDDEN)
        if not transport.can_be_rented:
            return Response({"detail": "Not fount: the matching transport can't be rented."},
                            status=status.HTTP_404_NOT_FOUND)
        query = request.GET
        rent_type = query.get('rentType')
        if rent_type not in Rent.CHOICES_TO_RENT.keys():
            return Response({"detail": "Bad request: rentType must be present (query) as ont of these string: 'Days', "
                                       "'Minutes'"},
                            status=status.HTTP_400_BAD_REQUEST)
        data = {"user_id": request.user.id,
                "price_of_unit": 0,
                "transport_id": transportId,  # here we use the value of ID -------->-------->------V
                "type": Rent.CHOICES_TO_RENT[rent_type]  #                                          |
                }  #                                                                                |
        serialized = self.serializer_class(None, data)  #     int ID is needed here <---------------|
        if not serialized.is_valid():  #                                                            |
            return Response({"detail": serialized.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data["user_id"] = request.user  # and here we use the user himself <----------<-------------<
        data["transport_id"] = transport  # it works anyway
        rent = self.serializer_class.create(self.serializer_class(), data)
        # If there's an active rent, the transport becomes unrentable
        TransportSerializer.update(TransportSerializer(), transport, {"can_be_rented": False})
        return Response(self.get_serializer(rent).data, status=status.HTTP_201_CREATED)


class EndRent(generics.GenericAPIView):
    """
    Ends an active rent, only available for the renter; query: lat, long (float)\n
    POST /api/Rent/End/{rentId}
    """
    allowed_methods = ["POST"]
    permission_classes = (IsAuthenticated,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Rent controller'],
                         manual_parameters=
                         [openapi.Parameter('rentId', in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER, required=True),
                          openapi.Parameter('lat', in_=openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True),
                          openapi.Parameter('long', in_=openapi.IN_QUERY, type=openapi.TYPE_NUMBER, required=True)],
                         responses={
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT),
                         })
    def post(self, request, rentId):
        rent = get_object_or_404(Rent, id=rentId)
        if rent.time_end:
            return Response({"detail": "Not found: the matching Rent had already been ended."},
                            status=status.HTTP_404_NOT_FOUND)
        query = request.GET
        lat, long = query.get('lat'), query.get('long')
        errors = ""
        try:
            lat = float(lat)
        except Exception:
            errors += "lat must be present (query) as a float; "
        try:
            long = float(long)
        except Exception:
            errors += "long must be present (query) as a float."
        if errors:
            return Response({"detail": "Bad request: " + errors},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.user != rent.user_id:
            return Response({"detail": "Only the renter can end the rent."},
                            status=status.HTTP_403_FORBIDDEN)
        # data = {"is_active": False}
        # serialized = self.serializer_class(None, data)
        # if not serialized.is_valid():
        #     return Response({"detail": serialized.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.serializer_class.update(self.serializer_class(), rent, {"time_end": datetime.now().utcnow()})
        transport = rent.transport_id
        TransportSerializer.update(TransportSerializer(), transport, {"latitude": lat, "longitude": long,
                                                                      "can_be_rented": True})
        return Response({"detail": "Ended the rent successfully."}, status=status.HTTP_200_OK)
