from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PaymentCard

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'first_name', 'last_name', 'email', 'phone_number',
            'profile_picture_url', 'address_longitude', 'address_latitude',
            'created_at', 'updated_at', 'is_active', 'is_chef'
        ]


class SignupSerializer(serializers.Serializer):
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)
    address_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    address_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    is_chef = serializers.BooleanField(default=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email already in use')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(
            **validated_data
        )
        user.set_password(password)
        user.save()
        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class PaymentCardSerializer(serializers.ModelSerializer):
    card_number = serializers.CharField(write_only=True, min_length=12, max_length=19)

    class Meta:
        model = PaymentCard
        fields = ['id', 'card_number', 'cardholder_name', 'exp_month', 'exp_year', 'is_default', 'created_at']
        read_only_fields = ['id', 'created_at']

    def create(self, validated_data):
        card_number = validated_data.pop('card_number')
        last4 = card_number[-4:]
        validated_data['card_last4'] = last4
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)
