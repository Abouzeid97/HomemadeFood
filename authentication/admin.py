from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import PaymentCard

User = get_user_model()


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'is_active', 'is_chef')
    search_fields = ('email', 'first_name', 'last_name', 'phone_number')


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_last4', 'cardholder_name', 'exp_month', 'exp_year', 'is_default')
    search_fields = ('user__email', 'card_last4')
