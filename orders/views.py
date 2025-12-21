from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import Order, OrderItem
from .serializers import (
    OrderCreateSerializer, OrderListSerializer, 
    OrderDetailSerializer, OrderUpdateSerializer
)
from authentication.models import User


class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderCreateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        # Ensure the authenticated user is the customer
        customer = self.request.user
        serializer.save(customer=customer)


class OrderListView(generics.ListAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        
        # Consumers can see their placed orders
        if hasattr(user, 'consumer'):
            return Order.objects.filter(customer=user)
        
        # Chefs can see orders assigned to them
        elif hasattr(user, 'chef'):
            return Order.objects.filter(chef=user)
        
        # For now, return empty queryset for other user types
        return Order.objects.none()


class OrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = OrderDetailSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'order_id'
    lookup_url_kwarg = 'order_id'

    def get_queryset(self):
        user = self.request.user
        
        # Consumers can see their own orders
        if hasattr(user, 'consumer'):
            return Order.objects.filter(customer=user)
        
        # Chefs can see orders assigned to them
        elif hasattr(user, 'chef'):
            return Order.objects.filter(chef=user)
        
        # For now, return empty queryset for other user types
        return Order.objects.none()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return OrderUpdateSerializer
        return OrderDetailSerializer

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if the authenticated user is the chef for this order
        if hasattr(request.user, 'chef') and instance.chef == request.user:
            # Chef can update the order status
            return super().update(request, *args, **kwargs)
        elif hasattr(request.user, 'consumer') and instance.customer == request.user:
            # Consumer can cancel the order if it's still pending or confirmed
            if instance.status in ['pending', 'confirmed'] and request.data.get('status') == 'cancelled':
                return super().update(request, *args, **kwargs)
            else:
                return Response(
                    {'error': 'You can only cancel pending or confirmed orders'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
        else:
            return Response(
                {'error': 'You do not have permission to update this order'}, 
                status=status.HTTP_403_FORBIDDEN
            )