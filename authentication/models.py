from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.utils import timezone


class UserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email address')
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone_number=phone_number,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, first_name, last_name, phone_number, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # common attributes
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20, unique=True)
    profile_picture_url = models.URLField(blank=True, null=True)
    address_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    address_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    # user type
    is_chef = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

    def __str__(self):
        return f"{self.email} ({self.first_name} {self.last_name})"


class PaymentCard(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='payment_cards')
    card_last4 = models.CharField(max_length=4)
    cardholder_name = models.CharField(max_length=128)
    exp_month = models.PositiveSmallIntegerField()
    exp_year = models.PositiveSmallIntegerField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"**** **** **** {self.card_last4} ({self.user.email})"


# Signals to toggle user active state based on presence of payment cards
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=PaymentCard)
def activate_user_on_card_save(sender, instance, created, **kwargs):
    if created:
        user = instance.user
        if not user.is_active:
            user.is_active = True
            user.save(update_fields=['is_active'])


@receiver(post_delete, sender=PaymentCard)
def maybe_deactivate_user_on_card_delete(sender, instance, **kwargs):
    user = instance.user
    if not user.payment_cards.exists():
        user.is_active = False
        user.save(update_fields=['is_active'])
