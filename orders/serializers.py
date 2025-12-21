from rest_framework import serializers
from .models import Order, OrderItem
from authentication.models import User
from dishes.models import Dish


class OrderItemSerializer(serializers.ModelSerializer):
    dish_name = serializers.CharField(source='dish.name', read_only=True)
    dish_description = serializers.CharField(source='dish.description', read_only=True)
    dish_price = serializers.DecimalField(source='dish.price', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'dish', 'dish_name', 'dish_description', 'dish_price', 'quantity', 'unit_price', 'special_requests']
        read_only_fields = ['unit_price']


class OrderCreateSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'customer', 'chef', 'total_amount', 'delivery_address', 
            'delivery_longitude', 'delivery_latitude', 'estimated_delivery_time', 
            'special_instructions', 'items', 'status'
        ]
        read_only_fields = ['order_id', 'status', 'total_amount']

    def create(self, validated_data):
        items_data = validated_data.pop('items')
        order = Order.objects.create(**validated_data)
        
        total_amount = 0
        for item_data in items_data:
            # Set the unit price to the current dish price
            dish = item_data['dish']
            item_data['unit_price'] = dish.price
            order_item = OrderItem.objects.create(order=order, **item_data)
            total_amount += order_item.get_subtotal()
        
        order.total_amount = total_amount
        order.save()
        return order


class OrderListSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    chef_name = serializers.CharField(source='chef.get_full_name', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'customer_name', 'chef_name', 'status', 'total_amount', 
            'created_at', 'items_count'
        ]

    def get_items_count(self, obj):
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    chef_name = serializers.CharField(source='chef.get_full_name', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'order_id', 'customer', 'customer_name', 'chef', 'chef_name', 'status', 
            'total_amount', 'delivery_address', 'delivery_longitude', 'delivery_latitude', 
            'estimated_delivery_time', 'special_instructions', 'created_at', 'updated_at', 'items'
        ]


class OrderUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
        
    def validate_status(self, value):
        # Add validation for status transitions if needed
        # For example, prevent going from 'delivered' back to 'pending'
        valid_transitions = {
            'pending': ['confirmed', 'cancelled'],
            'confirmed': ['preparing', 'cancelled'],
            'preparing': ['ready'],
            'ready': ['delivered'],
            'delivered': [],
            'cancelled': []
        }
        
        current_status = self.instance.status if self.instance else None
        if current_status and value != current_status and value not in valid_transitions.get(current_status, []):
            raise serializers.ValidationError(f'Cannot change status from {current_status} to {value}')
        
        return value