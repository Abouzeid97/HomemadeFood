from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from .models import Category, Dish, DishReview, DishImage

User = get_user_model()


class DishesModelTestCase(TestCase):
    """Test cases for dishes models"""

    def setUp(self):
        # Create a chef user
        self.chef = User.objects.create_user(
            email='chef@example.com',
            first_name='Chef',
            last_name='Test',
            phone_number='1234567890',
            password='testpassword123'
        )
        
        # Create a customer user
        self.customer = User.objects.create_user(
            email='customer@example.com',
            first_name='Customer',
            last_name='Test',
            phone_number='0987654321',
            password='testpassword123'
        )

    def test_category_creation(self):
        """Test creating a category"""
        category = Category.objects.create(
            name='Main Course',
            description='Delicious main courses'
        )
        
        self.assertEqual(category.name, 'Main Course')
        self.assertEqual(category.description, 'Delicious main courses')
        self.assertIsNotNone(category.created_at)

    def test_dish_creation(self):
        """Test creating a dish"""
        category = Category.objects.create(name='Appetizers')
        
        dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=category,
            price=Decimal('15.99'),
            preparation_time=30
        )
        
        self.assertEqual(dish.name, 'Test Dish')
        self.assertEqual(dish.chef, self.chef)
        self.assertEqual(dish.category, category)
        self.assertEqual(dish.price, Decimal('15.99'))
        self.assertTrue(dish.is_available)

    def test_dish_review_creation(self):
        """Test creating a dish review"""
        category = Category.objects.create(name='Main Course')
        
        dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=category,
            price=Decimal('15.99'),
            preparation_time=30
        )
        
        review = DishReview.objects.create(
            dish=dish,
            customer=self.customer,
            rating=5,
            review_text='Excellent dish!'
        )
        
        self.assertEqual(review.dish, dish)
        self.assertEqual(review.customer, self.customer)
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.review_text, 'Excellent dish!')

    def test_dish_image_creation(self):
        """Test creating a dish image"""
        category = Category.objects.create(name='Main Course')
        
        dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=category,
            price=Decimal('15.99'),
            preparation_time=30
        )
        
        image = DishImage.objects.create(
            dish=dish,
            image_url='https://example.com/image.jpg',
            is_primary=True
        )
        
        self.assertEqual(image.dish, dish)
        self.assertEqual(image.image_url, 'https://example.com/image.jpg')
        self.assertTrue(image.is_primary)


class DishesAPITestCase(APITestCase):
    """Test cases for dishes API endpoints"""

    def setUp(self):
        # Create users
        self.chef = User.objects.create_user(
            email='chef@example.com',
            first_name='Chef',
            last_name='Test',
            phone_number='1234567890',
            password='testpassword123'
        )
        
        self.customer = User.objects.create_user(
            email='customer@example.com',
            first_name='Customer',
            last_name='Test',
            phone_number='0987654321',
            password='testpassword123'
        )
        
        # Create a category and dish
        self.category = Category.objects.create(
            name='Main Course',
            description='Delicious main courses'
        )
        
        self.dish = Dish.objects.create(
            chef=self.chef,
            name='Test Dish',
            description='A delicious test dish',
            category=self.category,
            price=Decimal('15.99'),
            preparation_time=30
        )

    def test_get_categories_list(self):
        """Test getting list of categories"""
        url = reverse('category-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_dish_detail(self):
        """Test getting dish detail"""
        url = reverse('dish-detail', kwargs={'pk': self.dish.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Test Dish')

    def test_get_dishes_by_category(self):
        """Test getting dishes by category"""
        url = reverse('dishes-by-category', kwargs={'pk': self.category.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_dish_reviews(self):
        """Test getting dish reviews"""
        url = reverse('dish-reviews', kwargs={'dish_id': self.dish.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])