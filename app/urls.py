# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('register/user/', UserRegistrationView.as_view(), name='user-register'),
    path('register/merchant/', MerchantRegistrationView.as_view(), name='merchant-register'),
    path('biometric/setup/', BiometricDataView.as_view(), name='biometric-setup'),
    path('login/', LoginView.as_view(), name='login'),
    path("wallet/fund/", FundWalletAPIView.as_view(), name="fund_wallet"),
    path("wallet/callback/", WalletCallbackAPIView.as_view(), name="wallet_callback"),
]
