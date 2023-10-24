import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from .models import User


class JWTAuthentication(authentication.BaseAuthentication):
    authentication_header_prefix = 'Token'

    def authenticate(self, request):
        """
        The main method of authentication. Gets the token from headers and tries to auth. with it.
        :returns: (user, token) if success, else None (Exceptions are handled by DRF)
        """
        request.user = None

        auth_header = authentication.get_authorization_header(request).split()  # [prefix, token]
        auth_header_prefix = self.authentication_header_prefix.lower()  # the prefix is "token"

        if not auth_header:
            return None
        elif len(auth_header) != 2:
            # Incorrect amount of elements in the header (the correct one is 2)
            return None

        # JWT uses bytes, so we need to decode
        prefix, token = auth_header[0].decode('utf-8'), auth_header[1].decode('utf-8')

        if prefix.lower() != auth_header_prefix: # Wrong prefix (the only right one is Token)
            return None

        return self._authenticate_credentials(request, token)  # The auth goes on to the next method

    def _authenticate_credentials(self, request, token):
        """ Trying to authenticate with given token, raises an Exceptions if failures """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        except Exception as e:
            print(e)
            msg = 'Exception while decoding the token.'
            raise exceptions.AuthenticationFailed(msg)

        try:
            user = User.objects.get(pk=payload['id'])
        except User.DoesNotExist:
            msg = 'No matching users for this token were found.'
            raise exceptions.AuthenticationFailed(msg)

        if not user.is_active:
            msg = 'This user is inactive (was deleted).'
            raise exceptions.AuthenticationFailed(msg)
        return (user, token)  # this is what the main method returns too if the authentication is successful
