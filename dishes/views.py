from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg
from .models import Category, Dish, DishReview, DishImage
from .serializers import (
    CategorySerializer, DishSerializer, DishListSerializer, 
    DishReviewSerializer, DishImageSerializer
)
from authentication.models import User


class CategoryListView(generics.ListAPIView):
    """List all active categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class CategoryDetailView(generics.RetrieveAPIView):
    """Get detailed information about a specific category"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class DishByCategoryView(generics.ListAPIView):
    """List dishes in a specific category"""
    serializer_class = DishListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        category_id = self.kwargs['pk']
        queryset = Dish.objects.filter(
            category_id=category_id,
            is_available=True
        ).select_related('chef', 'category').prefetch_related('reviews')
        
        # Apply filters
        is_available = self.request.query_params.get('is_available', None)
        if is_available is not None:
            is_available = is_available.lower() == 'true'
            queryset = queryset.filter(is_available=is_available)
            
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset


class DishListView(generics.ListAPIView):
    """List all available dishes"""
    serializer_class = DishListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Dish.objects.filter(is_available=True).select_related('chef', 'category').prefetch_related('reviews')
        
        # Apply filters
        category_id = self.request.query_params.get('category', None)
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id)
            
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)
        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset


class DishDetailView(generics.RetrieveAPIView):
    """Get detailed information about a specific dish"""
    queryset = Dish.objects.all().select_related('chef', 'category').prefetch_related('reviews', 'images')
    serializer_class = DishSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]


class ChefCategoryListView(generics.ListCreateAPIView):
    """List and create categories for the authenticated chef"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only return categories created by the authenticated chef
        if hasattr(self.request.user, 'dishes'):
            # Get categories that have dishes created by this chef
            dish_categories = Dish.objects.filter(
                chef=self.request.user
            ).values_list('category_id', flat=True).distinct()
            return Category.objects.filter(id__in=dish_categories)
        return Category.objects.none()

    def perform_create(self, serializer):
        # Check if the user is a chef before allowing category creation
        user_type = self.request.user.get_user_type()
        if user_type != 'chef':
            raise permissions.PermissionDenied("Only chefs can create categories")
        serializer.save()


class ChefCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific category for the authenticated chef"""
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow access to categories that have dishes created by this chef
        return Category.objects.filter(
            dishes__chef=self.request.user
        ).distinct()


class ChefDishListView(generics.ListCreateAPIView):
    """List and create dishes for the authenticated chef"""
    serializer_class = DishListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user_type = self.request.user.get_user_type()
        if user_type != 'chef':
            return Dish.objects.none()
        return Dish.objects.filter(chef=self.request.user).select_related('category')

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DishSerializer
        return DishListSerializer

    def perform_create(self, serializer):
        # Check if the user is a chef before allowing dish creation
        user_type = self.request.user.get_user_type()
        if user_type != 'chef':
            raise permissions.PermissionDenied("Only chefs can create dishes")
        serializer.save(chef=self.request.user)


class ChefDishDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific dish for the authenticated chef"""
    serializer_class = DishSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Only allow access to dishes created by this chef
        return Dish.objects.filter(chef=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_dish_review(request, dish_id):
    """Add a review for a dish (requires customer authentication)"""
    dish = get_object_or_404(Dish, id=dish_id)
    
    # Check if the user is a customer
    user_type = request.user.get_user_type()
    if user_type != 'consumer':
        return Response(
            {'error': 'Only customers can submit reviews'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # Check if the user has already reviewed this dish
    existing_review = DishReview.objects.filter(
        dish=dish, 
        customer=request.user
    ).first()
    
    if existing_review:
        return Response(
            {'error': 'You have already reviewed this dish'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = DishReviewSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(dish=dish, customer=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticatedOrReadOnly])
def get_dish_reviews(request, dish_id):
    """Get all reviews for a dish"""
    dish = get_object_or_404(Dish, id=dish_id)
    reviews = DishReview.objects.filter(dish=dish).select_related('customer')
    serializer = DishReviewSerializer(reviews, many=True)
    return Response(serializer.data)