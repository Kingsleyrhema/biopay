from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .models import CustomUser, BiometricData, Wallet, Transaction
from rest_framework.permissions import IsAuthenticated
from .serializers import (
    UserRegistrationSerializer, 
    MerchantRegistrationSerializer,
    BiometricDataSerializer,
    LoginSerializer
)
from rest_framework.permissions import IsAuthenticated
import requests
import uuid
from django.conf import settings
from django.shortcuts import get_object_or_404





SQUAD_API_URL = "https://sandbox-api-d.squadco.com/transaction/initiate"
SQUAD_SECRET_KEY = "sandbox_sk_be32b5ee4411f5dbd46e0ac180523b316ae8608abda3"  # Replace with actual secret key

class UserRegistrationView(APIView):
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'email': user.email,
                'user_type': user.user_type,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MerchantRegistrationView(APIView):
    def post(self, request):
        serializer = MerchantRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            merchant = serializer.save()
            refresh = RefreshToken.for_user(merchant)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': merchant.id,
                'email': merchant.email,
                'merchant_id': merchant.merchant_id,
                'user_type': merchant.user_type,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class BiometricDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BiometricDataSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            biometric_data = serializer.save()
            return Response({'message': 'Biometric data stored successfully'}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            password = serializer.validated_data['password']

            user = CustomUser.objects.filter(email=email).first()
            if user and user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({'access': str(refresh.access_token)}, status=status.HTTP_200_OK)

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    

class FundWalletAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        amount = request.data.get("amount")

        if not amount or int(amount) <= 0:
            return Response({"error": "Invalid amount"}, status=400)

        transaction_ref = str(uuid.uuid4())  # Generate unique transaction ID

        payload = {
            "email": user.email,
            "amount": int(amount) * 100,  # Convert to kobo
            "currency": "NGN",
            "customer_name": user.username,
            "initiate_type": "inline",
            "transaction_ref": transaction_ref,
            "callback_url": "http://127.0.0.1/api/app/wallet/callback/",  # Update with your actual domain
            "payment_channels": ["card", "bank", "ussd"],
            "metadata": {"user_id": user.id}
        }

        headers = {
            "Authorization": f"Bearer {SQUAD_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(SQUAD_API_URL, json=payload, headers=headers)

        if response.status_code == 200:
            data = response.json().get("data")
            checkout_url = data.get("checkout_url")

            # Save transaction
            Transaction.objects.create(
                user=user,
                transaction_ref=transaction_ref,
                amount=amount,
                status="pending"
            )

            return Response({"checkout_url": checkout_url})
        else:
            return Response({"error": "Failed to initiate payment"}, status=400)
        
class WalletCallbackAPIView(APIView):
    def post(self, request):
        data = request.data
        transaction_ref = data.get("transaction_ref")
        status = data.get("status")  # Check Squad's webhook documentation for actual response

        transaction = get_object_or_404(Transaction, transaction_ref=transaction_ref)

        if status == "successful":
            transaction.status = "successful"
            transaction.save()

            # Update user wallet balance
            wallet, _ = Wallet.objects.get_or_create(user=transaction.user)
            wallet.balance += transaction.amount
            wallet.save()

            return Response({"message": "Wallet funded successfully!"})
        else:
            transaction.status = "failed"
            transaction.save()
            return Response({"error": "Payment failed"}, status=400)
