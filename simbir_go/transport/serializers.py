from rest_framework import serializers

from .models import Transport


class TransportSerializer(serializers.ModelSerializer):
    """ Transport model serializer """

    class Meta:
        model = Transport
        fields = ['can_be_rented', 'transport_type', 'model', 'color', 'identifier', 'description',
                  'latitude', 'longitude', 'minute_price', 'day_price', 'owner_id']
        lookup_field = 'model'

    def update(self, instance, validated_data):
        """ fields partial update method """

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()  # saving after committing changed

        return instance

    def create(self, validated_data):
        return Transport.objects.create(**validated_data)
