from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.viewsets import ViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import Transport
import json
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""

from .serializers import TransportSerializer


def read_transport_body(post_, all_required=True):  # This static function was made because validation is too long to rewrite it every time
    """
    Checks the given decoded JSON body for valid data that can be used for updating/creating a Transport Model.\n
    :param post_: (!) decoded JSON body of a HTTP request
    :return: True, transport_data_dict if data is valid,
    else False, Response(...400_BAD_REQUEST).
    transportType is also converted from readable to writeable version (choices are used for this field)
    """
    can_be_rented, transport_type, model, color, identifier,\
    description, latitude, longitude,\
    minute_price, day_price = post_.get("canBeRented"), post_.get("transportType"), post_.get('model'),\
                              post_.get('color'), post_.get('identifier'), post_.get('description'),\
                              post_.get('latitude'), post_.get('longitude'), post_.get('minutePrice'),\
                              post_.get('dayPrice')
    errors = ""  # If there's at least one variable that doesn't satisfy the requirements, we get 400 BAD REQUEST

    choices_dict = dict(Transport.TRANSPORT_CHOICES)
    if not (isinstance(can_be_rented, bool) or (can_be_rented is None and not all_required)):
        errors += "canBeRented must be present as a bool; "
    if not ((transport_type in choices_dict.values() or transport_type is None and not all_required) or
            (transport_type is None and not all_required)):
        errors += f"transportType must be equal to one of these: {', '.join(choices_dict.values())} " \
                  f"(or it may be null if PUT); "
    # elif transport_type not in choices_dict.values():
    #     errors += f"transportType must be equal to one of these: {', '.join(choices_dict.values())}; "

    if not (isinstance(model, str) or (model is None and not all_required)):
        errors += "model must be present as a string; "

    if not (isinstance(color, str) or (color is None and not all_required)):
        errors += "model must be present as a string; "

    if not (isinstance(identifier, str) or (identifier is None and not all_required)):
        errors += "identifier must be present as a string; "

    if not isinstance(description, str) and description is not None:
        errors += "description must either not be present or a be string; "

    if not (isinstance(latitude, float) or (latitude is None and not all_required)):
        errors += "latitude must be present as a float (double); "

    if not (isinstance(longitude, float) or (longitude is None and not all_required)):
        errors += "longitude must be present as a float (double); "

    if not isinstance(minute_price, float) and minute_price is not None:
        errors += "minutePrice must either not be present or a be float (double); "

    if not isinstance(day_price, float) and day_price is not None:
        errors += "day_price must either not be present or a be float (double); "

    if errors:
        return False, Response({"detail": "Bad request: " + errors}, status=status.HTTP_400_BAD_REQUEST)

    transport_type = Transport.CHOICE_TO_TRANSPORT[transport_type]
    data = {"can_be_rented": can_be_rented,
            "transport_type": transport_type,
            "model": model,
            "color": color,
            "identifier": identifier,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "minute_price": minute_price,
            "day_price": day_price
    }
    return True, data


class TransportCreate(generics.CreateAPIView):
    """
    Transport creating Api View (no permissions)\n
    POST /api/Transport - Creates a new transport
    """
    allowed_methods = ["POST"]
    permission_classes = (IsAuthenticated,)
    serializer_class = TransportSerializer
    queryset = Transport.objects.all()

    @swagger_auto_schema(tags=['Transport controller'],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             required=['canBeRented', 'transportType', 'model', 'color', 'identifier', 'latitude',
                                       'longitude'],
                             properties={
                                 'canBeRented': openapi.Schema('canBeRented', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_BOOLEAN),
                                 'transportType': openapi.Schema('transportType', in_=openapi.IN_BODY,
                                                                 type=openapi.TYPE_STRING),
                                 'model': openapi.Schema('model', in_=openapi.IN_BODY,
                                                         type=openapi.TYPE_STRING),
                                 'color': openapi.Schema('color', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 'identifier': openapi.Schema('identifier', in_=openapi.IN_BODY,
                                                                 type=openapi.TYPE_STRING),
                                 'description': openapi.Schema('description', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_STRING),
                                 'latitude': openapi.Schema('latitude', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_NUMBER),
                                 'longitude': openapi.Schema('longitude', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_NUMBER),
                                 'dayPrice': openapi.Schema('dayPrice', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_NUMBER),
                                 'minutePrice': openapi.Schema('minutePrice', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_NUMBER),
                             }),
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
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
        # this function returns False, Response(HTTP_400) if post_ is invalid, else True, (transport_fields)
        is_valid, response_400 = read_transport_body(post_)
        if not is_valid:  # if False is returned first, then Response is surely returned second
            return response_400
        data = response_400  # in case of is_valid = True, response_400 is a tuple with variables
        data["owner_id"] = request.user.id  # actually, this is the only field that's not stated in the body
        serialized = self.serializer_class(None, data)
        if not serialized.is_valid():
            return Response({"detail": serialized.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.serializer_class.create(self.serializer_class(), data)
        return Response(serialized.data, status=status.HTTP_201_CREATED)


class TransportViewSetWithId(ViewSet):
    """
    ViewSet of Transport controller actions that require <int:id> (no permissions)\n
    GET /api/Transport/{id} - get transport fields\n
    PUT /api/Transport/{id} - update transport fields\n
    DELETE /api/Transport/{id} - delete transport
    """
    allowed_methods = ["GET", "PUT", "DELETE"]
    permission_classes = (AllowAny,)
    serializer_class = TransportSerializer
    queryset = Transport.objects.all()

    @swagger_auto_schema(tags=['Transport controller'],
                         manual_parameters=[openapi.Parameter('id', in_=openapi.IN_PATH, required=True,
                                                              type=openapi.TYPE_INTEGER)],
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def get(self, request, id):
        transport = get_object_or_404(Transport, id=id)
        return Response(self.serializer_class(transport).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Transport controller'],
                         manual_parameters=[openapi.Parameter('id', in_=openapi.IN_PATH, required=True,
                                                              type=openapi.TYPE_INTEGER)],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             # required=['canBeRented', 'transportType', 'model', 'color', 'identifier', 'latitude',
                             #           'longitude'],
                             properties={
                                 'canBeRented': openapi.Schema('canBeRented', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_BOOLEAN),
                                 'transportType': openapi.Schema('transportType', in_=openapi.IN_BODY,
                                                                 type=openapi.TYPE_STRING),
                                 'model': openapi.Schema('model', in_=openapi.IN_BODY,
                                                         type=openapi.TYPE_STRING),
                                 'color': openapi.Schema('color', in_=openapi.IN_BODY, type=openapi.TYPE_STRING),
                                 'identifier': openapi.Schema('identifier', in_=openapi.IN_BODY,
                                                              type=openapi.TYPE_STRING),
                                 'description': openapi.Schema('description', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_STRING),
                                 'latitude': openapi.Schema('latitude', in_=openapi.IN_BODY,
                                                            type=openapi.TYPE_NUMBER),
                                 'longitude': openapi.Schema('longitude', in_=openapi.IN_BODY,
                                                             type=openapi.TYPE_NUMBER),
                                 'dayPrice': openapi.Schema('dayPrice', in_=openapi.IN_BODY,
                                                            type=openapi.TYPE_NUMBER),
                                 'minutePrice': openapi.Schema('minutePrice', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_NUMBER),
                             }),
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def put(self, request, id):
        transport = get_object_or_404(Transport, id=id)
        if not request.user.is_authenticated or transport.owner_id != request.user.id:
            return Response({"detail": "Only the owner of the transport can update it."},
                            status=status.HTTP_403_FORBIDDEN)
        put_ = request.data
        is_valid, response_400 = read_transport_body(put_)
        if not is_valid:  # if False is returned first, then Response is surely returned second
            return response_400
        data = response_400  # in case of is_valid = True, response_400 is a tuple with variables
        serialized = self.serializer_class(None, data)
        if not serialized.is_valid():
            return Response({"detail": serialized.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.serializer_class.update(self.serializer_class(), transport, data)
        return Response({"detail": "Updated fields successfully."}, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Transport controller'],
                         manual_parameters=[openapi.Parameter('id', in_=openapi.IN_PATH, required=True,
                                                              type=openapi.TYPE_INTEGER)],
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def delete(self, request, id):
        transport = get_object_or_404(Transport, id=id)
        if not request.user.is_authenticated or transport.owner_id != request.user.id:
            return Response({"detail": "Only the owner of the transport can delete it."},
                            status=status.HTTP_403_FORBIDDEN)
        transport.delete()
        return Response({"detail": "Deleted successfully."}, status=status.HTTP_200_OK)
