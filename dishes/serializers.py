from rest_framework import serializers
from .models import Category, Dish, DishReview, DishImage, DishVarietySection, DishVarietyOption
from authentication.models import User, Chef
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
    image = serializers.ImageField()

    class Meta:
        model = DishImage
        fields = ['id', 'image', 'is_primary', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class DishReviewSerializer(serializers.ModelSerializer):
    """Serializer for DishReview model"""
    customer = UserSerializer(read_only=True)
    
    class Meta:
        model = DishReview
        fields = ['id', 'dish', 'customer', 'rating', 'review_text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'customer', 'created_at', 'updated_at']


class DishListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing dishes"""
    chef = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'id', 'name', 'price', 'is_available',
            'preparation_time', 'chef', 'category', 
            'created_at', 'average_rating', 'image'
        ]
        read_only_fields = ['id', 'created_at']

    def get_chef(self, obj):
        return {
            'id': obj.chef.id,
            'first_name': obj.chef.first_name,
            'last_name': obj.chef.last_name
        }

    def get_category(self, obj):
        return {
            'id': obj.category.id,
            'name': obj.category.name
        }

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            return primary_image.image.url
        return None


class DishVarietyOptionSerializer(serializers.ModelSerializer):
    """Serializer for DishVarietyOption model"""
    class Meta:
        model = DishVarietyOption
        fields = ['id', 'name', 'price_adjustment', 'is_available']


class DishVarietySectionSerializer(serializers.ModelSerializer):
    """Serializer for DishVarietySection model"""
    options = DishVarietyOptionSerializer(many=True, read_only=True)

    class Meta:
        model = DishVarietySection
        fields = ['id', 'name', 'description', 'is_required', 'options']


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
    variety_sections = DishVarietySectionSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = [
            'id', 'chef', 'name', 'description', 'price', 'is_available',
            'preparation_time', 'category', 'category_id', 'images',
            'reviews', 'variety_sections', 'created_at', 'updated_at', 'average_rating'
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


# Homepage Serializers

class CategoryHomeSerializer(serializers.ModelSerializer):
    """Lightweight category serializer for homepage"""
    dish_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'description', 'dish_count']

    def get_dish_count(self, obj):
        return obj.dishes.filter(is_available=True).count()


class FeaturedDishSerializer(DishListSerializer):
    """Extended dish serializer for homepage featured dishes"""
    # Inherits image from DishListSerializer
    description = serializers.SerializerMethodField()
    chef = serializers.SerializerMethodField()

    class Meta(DishListSerializer.Meta):
        fields = DishListSerializer.Meta.fields + ['description', 'chef']

    def get_description(self, obj):
        return obj.description

    def get_chef(self, obj):
        return {
            'id': obj.chef.id,
            'first_name': obj.chef.first_name,
            'last_name': obj.chef.last_name,
            'profile_picture': obj.chef.profile_picture.url if obj.chef.profile_picture else None
        }


class TopChefSerializer(serializers.ModelSerializer):
    """Chef serializer for homepage"""
    user = serializers.SerializerMethodField()

    class Meta:
        model = Chef
        fields = ['id', 'user', 'rating', 'total_reviews', 'cuisine_specialties']

    def get_user(self, obj):
        return {
            'id': obj.user.id,
            'first_name': obj.user.first_name,
            'last_name': obj.user.last_name,
            'profile_picture': obj.user.profile_picture.url if obj.user.profile_picture else None
        }


class NewDishSerializer(serializers.ModelSerializer):
    """Lightweight dish serializer for new dishes"""
    chef_name = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()

    class Meta:
        model = Dish
        fields = ['id', 'name', 'description', 'price', 'chef_name', 'image', 'created_at']

    def get_chef_name(self, obj):
        return f"{obj.chef.first_name} {obj.chef.last_name}"

    def get_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            return primary_image.image.url
        return None


class HomePageSerializer(serializers.Serializer):
    """Aggregated homepage response"""
    categories = CategoryHomeSerializer(many=True)
    featured_dishes = FeaturedDishSerializer(many=True)
    top_chefs = TopChefSerializer(many=True)
    new_dishes = NewDishSerializer(many=True)