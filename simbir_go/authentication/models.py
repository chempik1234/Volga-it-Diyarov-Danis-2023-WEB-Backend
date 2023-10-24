import jwt

from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)

from django.db import models
from django.core.validators import MinValueValidator


class UserManager(BaseUserManager):
    def create_user(self, username: str, password: str, is_staff: bool = False, balance: float = 0.0):
        """
        Creates a new user with given parameters and returns the created model.
        """
        if username is None:
            raise TypeError('Exception: username is None.')
        elif isinstance(username, str) and not username.strip():
            raise ValueError("Exception: empty username.")

        if password is None:
            raise TypeError('Exception: password is None.')
        elif isinstance(password, str) and not password.strip():
            raise ValueError("Exception: empty password.")

        if is_staff is None:
            raise TypeError("Exception: is_admin is None.")
        if balance is None:
            raise TypeError("Exception: balance is None.")
        elif (isinstance(balance, float) or isinstance(balance, int)) and balance < 0:
            raise ValueError(f"Exception: balance must be >= 0, but the given value is {balance}")

        user = self.model(username=username, is_staff=is_staff, balance=float(balance))
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, username: str, password: str, balance: float = 0.0, is_staff: bool = True):
        """ Creates an admin, is_admin is True by default """
        if is_staff is None:
            raise TypeError("Exception: is_admin is None.")
        elif isinstance(is_staff, bool) and not is_staff:
            raise TypeError("Exception: is_admin is not True.")
        user = self.create_user(username, password, is_staff, balance)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(db_index=True, max_length=255, unique=True)
    password = models.CharField(max_length=255)
    is_staff = models.BooleanField(default=False)
    balance = models.FloatField(default=0.0, validators=[MinValueValidator(0.0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['password', 'balance', 'is_staff']

    objects = UserManager()

    def __str__(self):
        return f"User {self.username}{' (admin)' * self.is_staff} with balance that equals {self.balance}"

    @property
    def token(self):
        """ Gets the jwt token for given user """
        return self._generate_jwt_token()

    def get_full_name(self):
        """ Default method that returns only username instead of using name and surname. """
        return self.username

    def get_short_name(self):
        """ Default method that returns only username instead of using name and surname. """
        return self.username

    def _generate_jwt_token(self):
        """ Generates a 1-day JWT token """
        expire_datetime = datetime.now() + timedelta(days=1)

        token_ = jwt.encode({
            'id': self.pk,  # pk is for "primary key"
            'exp': int(expire_datetime.timestamp())
        }, settings.SECRET_KEY, algorithm='HS256')

        return token_  # .decode('utf-8')

    # def validate_balance(self, value):
    #     if not isinstance(value, float):
    #         return False
    #         # raise TypeError("User balance must be a float.")
    #     elif value < 0:
    #         raise ValueError("User balance must be >= 0.")
    #     return value
