"""
Simple test script to verify dish varieties functionality
"""
import os
import sys
import django

# Setup Django
sys.path.append('/home/sherif-abouzeid/Desktop/Personal/HomemadeFood')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HomemadeFood.settings')
django.setup()

from authentication.models import User
from dishes.models import Dish, Category, DishVarietySection, DishVarietyOption

def test_varieties():
    print("Testing dish varieties functionality...")

    # Create a test chef user
    chef, created = User.objects.get_or_create(
        email='test_chef@example.com',
        defaults={
            'first_name': 'Test',
            'last_name': 'Chef',
            'phone_number': '9876543210'  # Different phone number to avoid uniqueness constraint
        }
    )
    if created:
        chef.set_password('testpass123')
        chef.save()

        # Create a Chef profile for the user
        from authentication.models import Chef as ChefProfile
        ChefProfile.objects.get_or_create(user=chef)

    # Create a category
    category, created = Category.objects.get_or_create(
        name='Test Category',
        defaults={'description': 'A test category'}
    )

    # Create a dish
    dish, created = Dish.objects.get_or_create(
        chef=chef,
        name='Test Dish',
        defaults={
            'description': 'A test dish',
            'category': category,
            'price': 10.00,
            'preparation_time': 20
        }
    )
    
    # Create a variety section
    variety_section = DishVarietySection.objects.create(
        dish=dish,
        name='Size Options',
        description='Choose your preferred size',
        is_required=False
    )
    
    # Create variety options
    small_option = DishVarietyOption.objects.create(
        section=variety_section,
        name='Small',
        price_adjustment=0.00,
        is_available=True
    )
    
    medium_option = DishVarietyOption.objects.create(
        section=variety_section,
        name='Medium',
        price_adjustment=2.00,
        is_available=True
    )
    
    large_option = DishVarietyOption.objects.create(
        section=variety_section,
        name='Large',
        price_adjustment=4.00,
        is_available=True
    )
    
    print(f"Created dish: {dish.name}")
    print(f"Created variety section: {variety_section.name}")
    print(f"Created variety options: {[opt.name for opt in variety_section.options.all()]}")
    
    # Verify the relationships
    assert dish.variety_sections.count() == 1
    assert variety_section.options.count() == 3
    assert small_option.section.dish == dish
    assert medium_option.price_adjustment == 2.00
    
    print("All tests passed! Dish varieties functionality is working correctly.")

if __name__ == "__main__":
    test_varieties()