from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg
from .models import Category, Dish, DishReview, DishImage, DishVarietySection, DishVarietyOption
from .serializers import (
    CategorySerializer, DishSerializer, DishListSerializer,
    DishReviewSerializer, DishImageSerializer,
    DishVarietySectionSerializer, DishVarietyOptionSerializer
)
from .pagination import StandardResultsSetPagination
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




class DishListView(generics.ListAPIView):
    """
    List all available dishes with optional filtering:
    - ?category_name={category_name}: Filter by category name
    - ?is_available=true/false: Filter by availability
    - ?min_price={price}&max_price={price}: Filter by price range
    """
    serializer_class = DishListSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        queryset = Dish.objects.filter(is_available=True).select_related('chef', 'category').prefetch_related('reviews')

        # Apply category filter by name if specified
        category_name = self.request.query_params.get('category_name', None)
        if category_name is not None:
            queryset = queryset.filter(category__name__icontains=category_name)

        # Apply additional filters
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


class DishVarietySectionCreateView(generics.CreateAPIView):
    """Create a new variety section for a dish (only dish creator can access)"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']
        dish = get_object_or_404(Dish, id=dish_id)

        # Check if the authenticated user is the dish creator
        if dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety sections.")

        serializer.save(dish=dish)


class DishVarietySectionUpdateView(generics.UpdateAPIView):
    """Update a variety section (only dish creator can access)"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'section_id'

    def get_queryset(self):
        # Only allow updating sections of dishes created by the authenticated user
        return DishVarietySection.objects.filter(dish__chef=self.request.user)


class DishVarietySectionDeleteView(generics.DestroyAPIView):
    """Delete a variety section (only dish creator can access)"""
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'section_id'

    def get_queryset(self):
        # Only allow deleting sections of dishes created by the authenticated user
        return DishVarietySection.objects.filter(dish__chef=self.request.user)


class DishVarietyOptionCreateView(generics.CreateAPIView):
    """Create a new variety option within a section (only dish creator can access)"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        section_id = self.kwargs['section_id']
        section = get_object_or_404(DishVarietySection, id=section_id)

        # Check if the authenticated user is the dish creator
        if section.dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety options.")

        serializer.save(section=section)


class DishVarietyOptionUpdateView(generics.UpdateAPIView):
    """Update a variety option (only dish creator can access)"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'option_id'

    def get_queryset(self):
        # Only allow updating options of sections from dishes created by the authenticated user
        return DishVarietyOption.objects.filter(section__dish__chef=self.request.user)


class DishVarietyOptionDeleteView(generics.DestroyAPIView):
    """Delete a variety option (only dish creator can access)"""
    permission_classes = [IsAuthenticated]
    lookup_url_kwarg = 'option_id'

    def get_queryset(self):
        # Only allow deleting options of sections from dishes created by the authenticated user
        return DishVarietyOption.objects.filter(section__dish__chef=self.request.user)


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
        # Since this is accessed via /chef/ endpoint, we return dishes for the authenticated user
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
        # The pk parameter comes from the URL pattern
        return Dish.objects.filter(chef=self.request.user)




class ReviewListCreateView(generics.ListCreateAPIView):
    """List all reviews for a dish or create a new review"""
    serializer_class = DishReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        return DishReview.objects.filter(dish_id=dish_id).select_related('customer')

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        dish = get_object_or_404(Dish, id=dish_id)

        # Check if the user is a customer
        user_type = self.request.user.get_user_type()
        if user_type != 'consumer':
            raise permissions.PermissionDenied("Only customers can submit reviews")

        # Check if the user has already reviewed this dish
        existing_review = DishReview.objects.filter(
            dish=dish,
            customer=self.request.user
        ).first()

        if existing_review:
            raise permissions.PermissionDenied("You have already reviewed this dish")

        serializer.save(dish=dish, customer=self.request.user)


class DishVarietySectionListCreateView(generics.ListCreateAPIView):
    """List all variety sections for a dish or create a new section"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        return DishVarietySection.objects.filter(dish_id=dish_id)

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        dish = get_object_or_404(Dish, id=dish_id)

        # Check if the authenticated user is the dish creator
        if dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety sections.")

        serializer.save(dish=dish)


class DishVarietySectionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific variety section"""
    serializer_class = DishVarietySectionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        # Only allow access to sections of dishes created by the authenticated user
        return DishVarietySection.objects.filter(
            dish_id=dish_id,
            id=section_id,
            dish__chef=self.request.user
        )


class DishVarietyOptionListCreateView(generics.ListCreateAPIView):
    """List all options in a section or create a new option"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        return DishVarietyOption.objects.filter(
            section_id=section_id,
            section__dish_id=dish_id
        )

    def perform_create(self, serializer):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        section = get_object_or_404(DishVarietySection, id=section_id)

        # Verify that the section belongs to the specified dish
        if section.dish_id != dish_id:
            raise permissions.PermissionDenied("Invalid section for this dish")

        # Check if the authenticated user is the dish creator
        if section.dish.chef != self.request.user:
            raise permissions.PermissionDenied("Only the dish creator can add variety options.")

        serializer.save(section=section)


class DishVarietyOptionRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or delete a specific variety option"""
    serializer_class = DishVarietyOptionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        dish_id = self.kwargs['dish_id']  # Matches the URL parameter name
        section_id = self.kwargs['section_id']
        option_id = self.kwargs['option_id']
        # Only allow access to options of sections from dishes created by the authenticated user
        return DishVarietyOption.objects.filter(
            section__dish_id=dish_id,
            section_id=section_id,
            id=option_id,
            section__dish__chef=self.request.user
        )