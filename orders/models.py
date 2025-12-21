from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from authentication.models import User  # Using the existing User model
from dishes.models import Dish  # Using the existing Dish model
from decimal import Decimal
import uuid

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]

    id = models.BigAutoField(primary_key=True)
    order_id = models.UUIDField(unique=True, default=uuid.uuid4, editable=False)
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='placed_orders',
                                limit_choices_to={'consumer__isnull': False})  # Only consumers can place orders
    chef = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_orders',
                            limit_choices_to={'chef__isnull': False})  # Only chefs can receive orders
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_address = models.TextField()
    delivery_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    delivery_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    estimated_delivery_time = models.DateTimeField(null=True, blank=True)
    special_instructions = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.email} to {self.chef.email}"

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)  # Price at time of order
    special_requests = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.quantity}x {self.dish.name} in order {self.order.order_id}"

    def get_subtotal(self):
        return self.quantity * self.unit_price

    class Meta:
        unique_together = ('order', 'dish')  # Each dish can only appear once per order
