from django.db import models
from authentication.models import User


class Transport(models.Model):
    TRANSPORT_CHOICES = (
        (0, "Car"),
        (1, "Bike"),
        (2, "Scooter")
    )
    CHOICE_TO_TRANSPORT = {j: i for i, j in dict(TRANSPORT_CHOICES).items()}
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    can_be_rented = models.BooleanField(default=False)
    transport_type = models.IntegerField(choices=TRANSPORT_CHOICES, default=0)
    model = models.CharField(max_length=255)
    color = models.CharField(max_length=30)
    identifier = models.CharField(max_length=10)
    description = models.TextField(null=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    minute_price = models.FloatField(null=True)
    day_price = models.FloatField(null=True)
