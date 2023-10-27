from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.viewsets import ViewSet
from django.shortcuts import get_object_or_404
from django.db.models.expressions import F
from django.db.models import FloatField
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from transport.models import Transport
from authentication.models import User
from .models import Rent
import json, pytz
from datetime import datetime
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""
from drf_yasg.utils import swagger_auto_schema, no_body
from drf_yasg import openapi
""" QUERY PARAMS FOR THIS WEIRD SWAGGER"""

from transport.serializers import TransportSerializer
from .serializers import RentSerializer


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


def read_post(post_, all_required=True):
    data = {
        "transport_id": post_.get("transportId"),
        "user_id": post_.get("userId"),
        "time_start": post_.get("timeStart"),
        "time_end": post_.get("timeEnd"),
        "price_of_unit": post_.get("priceOfUnit"),
        "type": post_.get("priceType"),
        "final_price": post_.get("finalPrice")
    }
    errors = ""
    if not (isinstance(data["transport_id"], int) or (data["transport_id"] is None and not all_required)):
        errors += "transportId must be present as an int; "
    if not (isinstance(data["user_id"], int) or (data["user_id"] is None and not all_required)):
        errors += "userId must be present as an int; "
    elif data["user_id"] is not None and not User.objects.filter(id=data["user_id"]).exists():
        errors += "userId is present but doesn't match to any User; "

    try:
        data["time_start"] = pytz.utc.localize(datetime.fromisoformat(data["time_start"]))
    except Exception:
        if data["time_start"] or all_required:
            errors += "timeStart must be present as an ISO-format datetime; "
    try:
        if data["time_end"]:
            data["time_end"] = pytz.utc.localize(datetime.fromisoformat(data["time_end"]))
    except Exception:
        if data["time_end"]:
            errors += "timeEnd must either be absent or be present as an ISO-format datetime; "
    if not (isinstance(data["price_of_unit"], float) or (data["price_of_unit"] is None and not all_required)):
        errors += "priceOfUnit must be present as a float; "
    if not ((data["type"] in Rent.CHOICES_TO_RENT.keys()) or (data["type"] is None and not all_required)):
        errors += "price_type must be present as one of these strings: 'Days', 'Minutes'; "
    if data["final_price"] is not None and data["final_price"] != 0:
        errors += "finalPrice must either be absent or be equal to 0."
    if errors:
        return False, Response({"detail": "Bad request: " + errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        data_res = {}
        for i, j in data.items():
            if camel_case(i) in post_.keys():
                data_res[i] = j
        # if "timeEnd" not in post_.keys():
        #     data.pop("time_end")
        # if "finalPrice" not in post_.keys():
        #     data.pop("final_price")\
        return True, data_res


class AdminRentViewSetWithId(ViewSet):
    """
    ViewSet of Admin Rent Controller actions that require rentId (IsAdminUser)\n
    GET /api/Admin/Rent/{rentId} Get information about a rent using it's id\n
    PUT /api/Admin/Rent/{rentId} Update information about a rent using it's id\n
    DELETE /api/Admin/Rent/{rentId} Delede a rent using it's id
    """
    allowed_methods = ["GET", "PUT", "DELETE"]
    permission_classes = (IsAdminUser,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Admin rent controller'])
    def get(self, request, rentId):
        rent = get_object_or_404(Rent, id=rentId)
        serialized = self.serializer_class(rent)
        return Response(serialized.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Admin rent controller'],
                         operation_description="PUT /api/Admin/Rent/{rentId} "
                                               "Update information about a rent using it's id",
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             properties={
                                 'transport_id': openapi.Schema('transport_id', in_=openapi.IN_BODY,
                                                                type=openapi.TYPE_INTEGER,
                                                                description="Id of the rented transport."),
                                 'user_id': openapi.Schema('user_id', in_=openapi.IN_BODY, type=openapi.TYPE_INTEGER,
                                                           description="Id of the renter (a user)."),
                                 'time_start': openapi.Schema('time_start', in_=openapi.IN_BODY,
                                                              type=openapi.TYPE_STRING,
                                                              description="Rental start date-time (iso format)"),
                                 'time_end': openapi.Schema('time_end', in_=openapi.IN_BODY, type=openapi.TYPE_STRING,
                                                            description="Rental end date-time (iso format)"),
                                 'price_of_unit': openapi.Schema('price_of_unit', in_=openapi.IN_BODY,
                                                                 type=openapi.TYPE_NUMBER,
                                                                 description="Rental price (per minute or day)"),
                                 'type': openapi.Schema('type', in_=openapi.IN_BODY, type=openapi.TYPE_STRING,
                                                        description="Rental type (Days / Minutes)"),
                                 'final_price': openapi.Schema('final_price', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_INTEGER,
                                                               description="Rental final (total) price")
                             }),
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def put(self, request, rentId):
        rent = get_object_or_404(Rent, id=rentId)
        put_ = request.data
        is_valid, response_400 = read_post(put_, all_required=False)  # decode the JSON body and briefly validate it
        if not is_valid:  # if False is returned first, then Response is surely returned second
            return response_400
        data = response_400  # in case of is_valid = True, response_400 is a tuple with variables and not a response
        # serialized = self.serializer_class(None, data)
        # if not serialized.is_valid():
        #     return Response(serialized.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.serializer_class.update(self.serializer_class(), rent, data)
        return Response({"detail": "Updated fields successfully."}, status=status.HTTP_200_OK)

    @swagger_auto_schema(tags=['Admin rent controller'],
                         manual_parameters=[openapi.Parameter('rentId', in_=openapi.IN_PATH,
                                                              type=openapi.TYPE_INTEGER,
                                                              description="Id of the deleted rent")])
    def delete(self, request, rentId):
        rent = get_object_or_404(Rent, id=rentId)
        rent.delete()
        return Response({"details": "Successfully deleted."}, status=status.HTTP_200_OK)


class AdminUserHistory(generics.GenericAPIView):
    """
    Get user's rent history (IsAdmin)\n
    GET /api/Admin/Rent/UserHistory/{userId}
    """
    allowed_methods = ["GET"]
    permission_classes = (IsAdminUser,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Admin rent controller'],
                         manual_parameters=[openapi.Parameter('userId', in_=openapi.IN_PATH,
                                                              type=openapi.TYPE_INTEGER,
                                                              description="Id of the user whose rental history is "
                                                                          "got.")])
    def get(self, request, userId):
        queryset = Rent.objects.filter(user_id__id=userId)  # returns all rents made by current user
        serialized = self.serializer_class(queryset, many=True)  # Many=True is used because a list is needed
        return Response(serialized.data, status=status.HTTP_200_OK)


class AdminTransportHistory(generics.GenericAPIView):
    """
    Get a transport's rent history (IsAdmin)\n
    GET /api/Rent/admin/TransportHistory/{transportId}
    """
    allowed_methods = ["GET"]
    permission_classes = (IsAdminUser,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Admin rent controller'],
                         manual_parameters=[openapi.Parameter('transportId', in_=openapi.IN_PATH,
                                                              type=openapi.TYPE_INTEGER,
                                                              description="Id of the transport whose history is got")],
                         responses={
                             404: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})})
    def get(self, request, transportId):
        transport = get_object_or_404(Transport, id=transportId)
        queryset = Rent.objects.filter(transport_id=transport)
        serialized = self.serializer_class(queryset, many=True)  # Many=True is used because a list is needed
        return Response(serialized.data, status=status.HTTP_200_OK)


class AdminNewRent(generics.GenericAPIView):
    """
    Creates a rent [Minutes, Days] (IsAdminUser,)\n
    POST /api/Rent/New/{transportId} - Creates a new Rent
    """
    allowed_methods = ["POST"]
    permission_classes = (IsAdminUser,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Admin rent controller'],
                         request_body=openapi.Schema(
                             type=openapi.TYPE_OBJECT,
                             required=['transport_id', 'user_id', 'time_start', 'price_of_unit',
                                       'type'],
                             properties={
                                 'transport_id': openapi.Schema('transport_id', in_=openapi.IN_BODY,
                                                                type=openapi.TYPE_INTEGER,
                                                                description="Id of the rented transport."),
                                 'user_id': openapi.Schema('user_id', in_=openapi.IN_BODY, type=openapi.TYPE_INTEGER,
                                                           description="Id of the renter (a user)."),
                                 'time_start': openapi.Schema('time_start', in_=openapi.IN_BODY,
                                                              type=openapi.TYPE_STRING,
                                                              description="Rental start date-time (iso format)"),
                                 'time_end': openapi.Schema('time_end', in_=openapi.IN_BODY, type=openapi.TYPE_STRING,
                                                            description="Rental end date-time (iso format)"),
                                 'price_of_unit': openapi.Schema('price_of_unit', in_=openapi.IN_BODY,
                                                                 type=openapi.TYPE_NUMBER,
                                                                 description="Rental price (per minute or day)"),
                                 'type': openapi.Schema('type', in_=openapi.IN_BODY, type=openapi.TYPE_STRING,
                                                        description="Rental type (Days / Minutes)"),
                                 'final_price': openapi.Schema('final_price', in_=openapi.IN_BODY,
                                                               type=openapi.TYPE_INTEGER,
                                                               description="Rental final (total) price")
                             }),
                         responses={
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             500: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)})
                         })
    def post(self, request):
        try:  # json body needs to be decoded, but if it contains syntax errors, an exception occures
            body_unicode = request.body.decode('utf-8')
            post_ = json.loads(body_unicode)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        is_valid, data = read_post(post_)
        if not is_valid:  # in this case an HTTP_400 Response is returned instead of data
            return data  # Response(status=400)
        transport = get_object_or_404(Transport, id=data["transport_id"])
        serialized = self.serializer_class(None, data)
        if not serialized.is_valid():
            return Response({"detail": serialized.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        data["transport_id"] = transport
        data["user_id"] = get_object_or_404(User, id=data["user_id"])
        # data["transport_id"] = transport.id
        # data["user_id"] = data["user_id"].id
        rent = self.serializer_class.create(self.serializer_class(), data)

        # If there's an active rent, the transport becomes unrentable
        if data["time_end"] and pytz.utc.localize(datetime.now().utcnow()) < data["time_end"]:
            TransportSerializer.update(TransportSerializer(), transport, {"can_be_rented": False})
        return Response(self.get_serializer(rent).data, status=status.HTTP_201_CREATED)


class AdminEndRent(generics.GenericAPIView):
    """
    Ends an active rent; query: lat, long (float) (IsAdminUser)\n
    POST /api/Rent/End/{rentId}
    """
    allowed_methods = ["POST"]
    permission_classes = (IsAdminUser,)
    serializer_class = RentSerializer
    queryset = Rent.objects.all()

    @swagger_auto_schema(tags=['Admin rent controller'],
                         manual_parameters=[openapi.Parameter('rentId', in_=openapi.IN_PATH, type=openapi.TYPE_INTEGER,
                                                              required=True,
                                                              description="Id of the rent which is ended"),
                                            openapi.Parameter('lat', in_=openapi.IN_QUERY, type=openapi.TYPE_NUMBER,
                                                              required=True,
                                                              description="Current latitude of the rented transport"),
                                            openapi.Parameter('long', in_=openapi.IN_QUERY, type=openapi.TYPE_NUMBER,
                                                              required=True,
                                                              description="Current longitude of the rented transport")],
                         request_body=no_body,
                         # required=['rentId', 'lat', 'long'],
                         responses={
                             200: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             400: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             403: openapi.Schema(type=openapi.TYPE_OBJECT,
                                                 properties={'detail': openapi.Schema(type=openapi.TYPE_STRING)}),
                             404: openapi.Schema(type=openapi.TYPE_OBJECT)
                         })
    def post(self, request, rentId):
        rent = get_object_or_404(Rent, id=rentId)
        if not rent.is_active:
            return Response({"detail": "Not found: the matching Rent had already been ended."}, status=status.HTTP_404_NOT_FOUND)
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
            return Response({"detail": "Bad request: " + errors}, status=status.HTTP_400_BAD_REQUEST)

        data = {"time_end": timezone.now()}
        # serialized = self.serializer_class(None, data)
        # if not serialized.is_valid():
        #     return Response({"detail":serialized.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.serializer_class.update(self.serializer_class(), rent, data)
        transport = rent.transport_id
        TransportSerializer.update(TransportSerializer(), transport, {"latitude": lat, "longitude": long,
                                                                      "can_be_rented": True})
        return Response({"detail": "Ended the rent successfully."}, status=status.HTTP_200_OK)
