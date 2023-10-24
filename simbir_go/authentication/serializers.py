from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    """ Custom user model serializer """
    password = serializers.CharField(
        max_length=255,
        min_length=8,
        write_only=True
    )

    class Meta:
        model = User
        fields = ['username', 'password', 'is_staff', 'balance', 'token']
        read_only_fields = ('token',)
        lookup_field = 'username'

    def update(self, instance, validated_data):
        """ fields partial update method """
        password = validated_data.pop('password', None)

        for key, value in validated_data.items():
            setattr(instance, key, value)

        if password is not None:
            instance.set_password(password)  # set_password method is more secure

        instance.save()  # saving after committing changed

        return instance

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

# class UsersSerializer(serializers.Serializer):
#     items = serializers.ListField(child=UserSerializer())
