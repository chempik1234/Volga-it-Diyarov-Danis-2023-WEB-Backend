from rest_framework import serializers
from datetime import datetime

from .models import Rent
from authentication.models import User


class RentSerializer(serializers.ModelSerializer):
    """ Rent model serializer """
    user_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=False)
    type = serializers.SerializerMethodField()

    class Meta:
        model = Rent
        fields = ['user_id', 'transport_id', 'type', 'time_start', 'time_end', 'price_of_unit',
                  'final_price']

    def update(self, instance, validated_data):
        """ fields partial update method """

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()  # saving after committing changed

        return instance

    def create(self, validated_data):
        return Rent.objects.create(**validated_data)

    def get_type(self, obj):
        return obj.get_type_display()
