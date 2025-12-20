from rest_framework import serializers
from .models import Category, Dish, DishReview, DishImage
from authentication.models import User
from authentication.serializers import UserSerializer


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    dish_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'dish_count']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_dish_count(self, obj):
        """Get the number of dishes in this category"""
        return obj.dishes.count()


class DishImageSerializer(serializers.ModelSerializer):
    """Serializer for DishImage model"""
    class Meta:
        model = DishImage
        fields = ['id', 'image_url', 'is_primary', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DishReviewSerializer(serializers.ModelSerializer):
    """Serializer for DishReview model"""
    customer = UserSerializer(read_only=True)
    
    class Meta:
        model = DishReview
        fields = ['id', 'dish', 'customer', 'rating', 'review_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']


class DishListSerializer(serializers.ModelSerializer):
    """Lighter serializer for listing dishes"""
    chef = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'description', 'price', 'is_available', 
            'preparation_time', 'chef', 'category', 'created_at', 
            'updated_at', 'average_rating'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        """Calculate average rating for the dish"""
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0


class DishSerializer(serializers.ModelSerializer):
    """Serializer for Dish model"""
    chef = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), 
        write_only=True,
        source='category'
    )
    images = DishImageSerializer(many=True, read_only=True)
    reviews = DishReviewSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = Dish
        fields = [
            'id', 'chef', 'name', 'description', 'price', 'is_available', 
            'preparation_time', 'category', 'category_id', 'images', 
            'reviews', 'created_at', 'updated_at', 'average_rating'
        ]
        read_only_fields = ['id', 'chef', 'created_at', 'updated_at']
    
    def get_average_rating(self, obj):
        """Calculate average rating for the dish"""
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

    def create(self, validated_data):
        """Create a new dish with the authenticated chef"""
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            validated_data['chef'] = request.user
        return super().create(validated_data)