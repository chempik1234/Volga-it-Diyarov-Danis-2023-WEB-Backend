from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.viewsets import ViewSet
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .models import Transport
from authentication.models import User
import json
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""

from .serializers import TransportSerializer


def camel_case(i: str):
    """
    Creates a camelCase string based on a snake_case string
    :param i: a snake_case string
    :return: a camelCase str
    """
    s, t = '', False
    for j in i:
        if j == '_':
            t = True
        else:
            if t:
                s += j.upper()
            else:
                s += j
            t = False
    return s


# This static function was made because validation is too long to rewrite it every time
def read_transport_body(post_, all_required=True):
    """
    Checks the given decoded JSON body for valid data that can be used for updating/creating a Transport Model.\n
    :param post_: (!) decoded JSON body of a HTTP request
    :param all_required: True by default, defines if all non-null fields in the HTTP body are required.
    But if the variable type is incorrect (bool, but needed float), a Response(HTTP_400) is still returned.\n
    :return: ( True, transport_data_dict ) if data is valid,  else ( False, Response(...400_BAD_REQUEST) ).
    transportType is also converted from readable to writeable version (choices are used for this field)
    """
    owner_id, can_be_rented, transport_type, model, color, identifier,\
    description, latitude, longitude,\
    minute_price, day_price = post_.get("ownerId"), post_.get("canBeRented"), post_.get("transportType"),\
                              post_.get('model'), post_.get('color'), post_.get('identifier'),\
                              post_.get('description'), post_.get('latitude'), post_.get('longitude'),\
                              post_.get('minutePrice'), post_.get('dayPrice')
    errors = ""  # If there's at least one variable that doesn't satisfy the requirements, we get 400 BAD REQUEST

    choices_dict = dict(Transport.TRANSPORT_CHOICES)
    if not (isinstance(owner_id, int) or (owner_id is None and not all_required)):
        errors += "ownerId must be present as an int; "
    elif not User.objects.filter(id=owner_id).exists() and owner_id is not None:
        errors += "ownerId is present but doesn't match to any user; "
    if not (isinstance(can_be_rented, bool) or (can_be_rented is None and not all_required)):
        errors += "canBeRented must be present as a bool; "
    if not (isinstance(transport_type, str) or (transport_type is None and not all_required)):
        errors += "transportType must be present as a string; "
    elif transport_type not in choices_dict.values() and transport_type is not None:
        errors += f"transportType must be equal to one of these: {', '.join(choices_dict.values())}; "

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

    transport_type = Transport.CHOICE_TO_TRANSPORT.get(transport_type)
    data = {"owner_id": owner_id,
            "owner": owner_id,
            "can_be_rented": can_be_rented,
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
    # There are 2 cases why a null=True field is None: (1) it's null in the body, but it is there;
    # (2) it's absent because it's PUT (all_required=False). So, we need to check if it's present and use it even if
    # it's None
    data_result = {}
    for i, j in data.items():
        if camel_case(i) in post_.keys():
            data_result[i] = j
    return True, data_result


class AdminTransportViewSetWithoutId(ViewSet):
    """
    ViewSet of Transport Controller actions that don't require <int:id> (IsAdminUser)\n
    GET /api/Admin/Transport?start=int&count=int&transportType=[Car,Bike,Scooter,All] - Get transport, where: id's in range (start, start + count) and displayable format of type is transportType\n
    POST /api/Admin/Transport - Creates a new transport
    """
    allowed_methods = ["GET", "POST"]
    permission_classes = (IsAdminUser,)
    serializer_class = TransportSerializer
    queryset = Transport.objects.all()

    @swagger_auto_schema(tags=['Admin transport controller'],
                         manual_parameters=[openapi.Parameter('start', in_=openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                                                              description="Id which transports are counted from"),
                                            openapi.Parameter('count', in_=openapi.IN_QUERY, type=openapi.TYPE_INTEGER,
                                                              description="Selection size (amount of id's)"),
                                            openapi.Parameter('transportType', in_=openapi.IN_QUERY,
                                                              type=openapi.TYPE_STRING,
                                                              description="Type of the transport (Car / Bike / Scooter "
                                                                          "/ All)")],
                         request_body=no_body,
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}, ),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def get(self, request):
        query = request.GET
        start, count, transport_type = query.get('start'), query.get('count'), query.get('transportType')
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

        if transport_type not in dict(Transport.TRANSPORT_CHOICES).values() and transport_type != "All":
            errors += "Parameter named 'transportType' must be present as a str (1 of these: 'Car', 'Bike', 'Scooter'" \
                      " or 'All')."

        if errors:
            return Response({"detail": "Bad request: " + errors}, status=status.HTTP_400_BAD_REQUEST)
        queryset = self.queryset.filter(id__gte=int(start), id__lt=int(start) + int(count))
        if transport_type != "All":
            queryset = queryset.filter(transport_type=Transport.CHOICE_TO_TRANSPORT[transport_type])
        serialized = self.serializer_class(queryset, many=True)  # Many=True is used because a list is needed
        return Response(serialized.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Admin transport controller'],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             required=['ownerId', 'canBeRented', 'transportType', 'model', 'color', 'identifier',
                                       'latitude', 'longitude'],
                             properties={
                                 'ownerId': openapi.Schema('ownerId', in_=openapi.IN_BODY,
                                                           type=openapi.TYPE_INTEGER,
                                                           description="Id of the transport owner"),
                                 'canBeRented': openapi.Schema('canBeRented', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_BOOLEAN,
                                                               description="Determines if the transport can be rented "
                                                                           "(false when there's an active rent!)"),
                                 'transportType': openapi.Schema('transportType', in_=openapi.IN_BODY,
                                                                 type=openapi.TYPE_STRING,
                                                                 description="Type of the transport (Car / Bike / Scoot"
                                                                             "er"),
                                 'model': openapi.Schema('model', in_=openapi.IN_BODY,
                                                         type=openapi.TYPE_STRING, description="Transport's model title"),
                                 'color': openapi.Schema('color', in_=openapi.IN_BODY, type=openapi.TYPE_STRING,
                                                         description="Color of the transport"),
                                 'identifier': openapi.Schema('identifier', in_=openapi.IN_BODY,
                                                              type=openapi.TYPE_STRING,
                                                              description="License plate"),
                                 'description': openapi.Schema('description', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_STRING,
                                                               description="Transport's description"),
                                 'latitude': openapi.Schema('latitude', in_=openapi.IN_BODY,
                                                            type=openapi.TYPE_NUMBER,
                                                            description="Transport's current latitude"),
                                 'longitude': openapi.Schema('longitude', in_=openapi.IN_BODY,
                                                             type=openapi.TYPE_NUMBER,
                                                             description="Transport's current longitude"),
                                 'dayPrice': openapi.Schema('dayPrice', in_=openapi.IN_BODY,
                                                            type=openapi.TYPE_NUMBER,
                                                            description="The price of a minute of a rent"),
                                 'minutePrice': openapi.Schema('minutePrice', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_NUMBER,
                                                               description="The price of a day of a rent"),
                             }),
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}, ),
                             500: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
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
        serialized = self.serializer_class(None, data)
        print(data)
        if not serialized.is_valid():
            return Response({"detail": serialized.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.serializer_class.create(self.serializer_class(), data)
        return Response(serialized.data, status=status.HTTP_201_CREATED)


class AdminTransportViewSetWithId(ViewSet):
    """
    ViewSet of Transport controller actions that require <int:id> (IsAdmin)\n
    GET /api/Admin/Transport/{id} - get transport fields\n
    PUT /api/Admin/Transport/{id} - update transport fields\n
    DELETE /api/Admin/Transport/{id} - delete transport
    """
    allowed_methods = ["GET", "PUT", "DELETE"]
    permission_classes = (IsAdminUser,)
    serializer_class = TransportSerializer
    queryset = Transport.objects.all()

    @swagger_auto_schema(tags=['Admin transport controller'],
                         operation_description="GET /api/Admin/Transport/{id} - get transport fields",
                         manual_parameters=[openapi.Parameter('id', type=openapi.TYPE_INTEGER, in_=openapi.IN_PATH)],
                         responses={
                             # 200: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}, ),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def get(self, request, id):
        transport = get_object_or_404(Transport, id=id)
        return Response(self.serializer_class(transport).data, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Admin transport controller'],
                         operation_description="PUT /api/Admin/Transport/{id} - update transport fields",
                         manual_parameters=[openapi.Parameter('id', type=openapi.TYPE_INTEGER, in_=openapi.IN_PATH)],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             # required=['ownerId', 'canBeRented', 'transportType', 'model', 'color', 'identifier',
                             #           'latitude', 'longitude'],
                             properties={
                                 'ownerId': openapi.Schema('ownerId', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_INTEGER),
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
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}, ),
                             # 500: openapi.Schema(type=openapi.TYPE_OBJECT,
                             #                     properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                         })
    def put(self, request, id):
        transport = get_object_or_404(Transport, id=id)
        put_ = request.data
        is_valid, response_400 = read_transport_body(put_, all_required=False)  # decode the JSON body and
        # briefly validate it
        if not is_valid:  # if False is returned first, then Response is surely returned second
            return response_400
        data = response_400  # in case of is_valid = True, response_400 is a tuple with variables and not a response
        # serialized = self.serializer_class(None, data)
        # if not serialized.is_valid():
        #     return Response(serialized.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.serializer_class.update(self.serializer_class(), transport, data)
        return Response({"detail": "Updated fields successfully."}, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Admin transport controller'],
                         operation_description="DELETE /api/Admin/Transport/{id} - delete transport",
                         manual_parameters=[openapi.Parameter('id', type=openapi.TYPE_INTEGER, in_=openapi.IN_PATH)],
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}, ),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT)})
    def delete(self, request, id):
        transport = get_object_or_404(Transport, id=id)
        transport.delete()
        return Response({"detail": "Deleted successfully."}, status=status.HTTP_200_OK)
