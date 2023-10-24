from django.db import models
from authentication.models import User
from transport.models import Transport


class Rent(models.Model):
    RENT_TYPE_CHOICES = ((False, "Minutes"),
                         (True, "Days"))
    CHOICES_TO_RENT = {"Minutes": False, "Days": True}
    # owner_id = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner")
    user_id = models.ForeignKey(User, on_delete=models.CASCADE)
    transport_id = models.ForeignKey(Transport, on_delete=models.CASCADE)
    type = models.BooleanField(choices=RENT_TYPE_CHOICES)
    # is_active = models.BooleanField(default=True)
    time_start = models.DateTimeField(auto_now=True)
    time_end = models.DateTimeField(null=True)
    price_of_unit = models.FloatField()
    final_price = models.FloatField(null=True)
