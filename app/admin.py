from django.contrib import admin
from .models import CustomUser, BiometricData, Wallet

admin.site.register(

    CustomUser
)


admin.site.register(

   BiometricData
)


admin.site.register(

  Wallet
)

# Register your models here.
