from django.urls import path
from . import views

urlpatterns = [
    # Public read-only endpoints
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/<int:pk>/', views.CategoryDetailView.as_view(), name='category-detail'),
    path('categories/<int:pk>/dishes/', views.DishByCategoryView.as_view(), name='dishes-by-category'),
    path('dishes/', views.DishListView.as_view(), name='dish-list'),
    path('dishes/<int:pk>/', views.DishDetailView.as_view(), name='dish-detail'),

    # Chef endpoints (Full CRUD)
    path('chef/categories/', views.ChefCategoryListView.as_view(), name='chef-category-list'),
    path('chef/categories/<int:pk>/', views.ChefCategoryDetailView.as_view(), name='chef-category-detail'),
    path('chef/dishes/', views.ChefDishListView.as_view(), name='chef-dish-list'),
    path('chef/dishes/<int:pk>/', views.ChefDishDetailView.as_view(), name='chef-dish-detail'),

    # Variety endpoints
    path('dishes/<int:dish_id>/sections/', views.DishVarietySectionCreateView.as_view(), name='dish-variety-section-create'),
    path('dishes/sections/<int:section_id>/', views.DishVarietySectionUpdateView.as_view(), name='dish-variety-section-update'),
    path('dishes/sections/<int:section_id>/delete/', views.DishVarietySectionDeleteView.as_view(), name='dish-variety-section-delete'),
    path('dishes/sections/<int:section_id>/options/', views.DishVarietyOptionCreateView.as_view(), name='dish-variety-option-create'),
    path('dishes/options/<int:option_id>/', views.DishVarietyOptionUpdateView.as_view(), name='dish-variety-option-update'),
    path('dishes/options/<int:option_id>/delete/', views.DishVarietyOptionDeleteView.as_view(), name='dish-variety-option-delete'),

    # Review endpoints
    path('dishes/<int:dish_id>/reviews/', views.get_dish_reviews, name='dish-reviews'),
    path('dishes/<int:dish_id>/reviews/add/', views.add_dish_review, name='add-dish-review'),
]