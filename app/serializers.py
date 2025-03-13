from rest_framework import serializers
from .models import CustomUser, BiometricData, Wallet
from django.utils.crypto import get_random_string

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'first_name', 'last_name', 'email', 'username', 'password', 'confirm_password', 'phone_number', 'nin')
        extra_kwargs = {
            'password': {'write_only': True},
            'nin': {'required': True},
            'phone_number': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone_number=validated_data['phone_number'],
            nin=validated_data['nin'],
            user_type='user'
        )
        user.set_password(validated_data['password'])
        user.save()

        Wallet.objects.create(user=user)
        return user

class MerchantRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    owner_name = serializers.CharField(write_only=True)
    owner_nin = serializers.CharField(write_only=True)

    class Meta:
        model = CustomUser
        fields = ('id', 'business_name', 'business_type', 'owner_name', 'owner_nin', 'email', 'username', 'password', 'confirm_password', 'phone_number')
        extra_kwargs = {
            'password': {'write_only': True},
            'business_name': {'required': True},
            'business_type': {'required': True},
            'phone_number': {'required': True},
        }

    def validate(self, data):
        if data['password'] != data.pop('confirm_password'):
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        merchant_id = 'M' + get_random_string(length=8, allowed_chars='0123456789')
        
        owner_name = validated_data.pop('owner_name')
        owner_nin = validated_data.pop('owner_nin')

        name_parts = owner_name.split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            phone_number=validated_data['phone_number'],
            business_name=validated_data['business_name'],
            business_type=validated_data['business_type'],
            merchant_id=merchant_id,
            first_name=first_name,
            last_name=last_name,
            nin=owner_nin,
            user_type='merchant'
        )
        user.set_password(validated_data['password'])
        user.save()

        Wallet.objects.create(user=user)
        return user

class BiometricDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = BiometricData
        fields = ('id', 'face_template', 'fingerprint_template')

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
