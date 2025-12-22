# Orders Module: Food Ordering System

## Overview
The orders module manages the complete food ordering workflow for the Homemade Food platform. It allows consumers to place orders with chefs, track order status, and handle order fulfillment from the chef's perspective.

### Architecture

```
Order (customer, chef, status, total_amount, delivery_info)
├── OrderItem (dish, quantity, unit_price, special_requests)
```

## Database Changes

Run migrations to create the orders-related tables:

```bash
python manage.py makemigrations orders
python manage.py migrate
```

## Core Models

### Order Model
- `order_id`: UUID for unique order identification
- `customer`: Foreign key to the User (consumer) who placed the order
- `chef`: Foreign key to the User (chef) who will fulfill the order
- `status`: Current status of the order (pending, confirmed, preparing, ready, delivered, cancelled)
- `total_amount`: Total cost of the order
- `delivery_address`: Address where the order should be delivered
- `delivery_longitude`/`delivery_latitude`: Geolocation for delivery
- `estimated_delivery_time`: Estimated time of delivery
- `special_instructions`: Any special instructions from the customer
- `created_at`/`updated_at`: Timestamps for tracking

### OrderItem Model
- `order`: Foreign key to the Order this item belongs to
- `dish`: Foreign key to the Dish ordered
- `quantity`: Number of this dish in the order
- `unit_price`: Price of the dish at the time of order
- `special_requests`: Any special requests for this dish item

## API Endpoints

All orders endpoints are accessible under the `/api/orders/` base path:

- `GET /api/orders/` - List orders for the authenticated user
  - For consumers: Returns orders placed by the user
  - For chefs: Returns orders received by the user
  - Optional query parameters: `status`, `date_range`

- `POST /api/orders/` - Create a new order (consumer only)
  - Required: `items` (list of dish_id, quantity), `delivery_address`, `delivery_longitude`, `delivery_latitude`
  - Optional: `special_instructions`, `estimated_delivery_time`
  - Requires authentication as a consumer

- `GET /api/orders/<order_id>/` - Get details of a specific order
  - Returns complete order details including items and status

- `PUT /api/orders/<order_id>/` - Update an order (chef only)
  - Only allowed to update status and estimated delivery time
  - Requires authentication as the chef assigned to the order

- `PATCH /api/orders/<order_id>/status/` - Update only the order status (chef only)
  - Required: `status` (one of pending, confirmed, preparing, ready, delivered, cancelled)
  - Requires authentication as the chef assigned to the order

- `DELETE /api/orders/<order_id>/` - Cancel an order (consumer only, if status is pending)
  - Requires authentication as the consumer who placed the order

- `GET /api/orders/<order_id>/tracking/` - Get real-time order tracking information
  - Returns status history and estimated delivery time

## Admin Interface

- **Orders**: View all orders, filter by status, customer, chef, date range
- **Order Items**: View all order items, useful for analytics and reporting

## Best Practices

### For Consumers
- Provide clear delivery addresses and coordinates
- Include special instructions for dishes when needed
- Monitor order status and communicate with chefs if needed
- Review dishes after order completion

### For Chefs
- Update order status promptly as it changes
- Provide accurate estimated delivery times
- Communicate with customers about any delays or issues
- Keep dishes updated in the menu to avoid ordering unavailable items

### Order Status Workflow
1. `pending` - Order placed, awaiting chef confirmation
2. `confirmed` - Chef has accepted the order
3. `preparing` - Chef is preparing the order
4. `ready` - Order is ready for delivery/pickup
5. `delivered` - Order has been delivered to the customer
6. `cancelled` - Order was cancelled (by customer or chef)

### Querying Orders

**Get orders for a customer:**
```python
customer_orders = Order.objects.filter(customer=user)
```

**Get orders for a chef:**
```python
chef_orders = Order.objects.filter(chef=user)
```

**Get orders by status:**
```python
pending_orders = Order.objects.filter(status='pending')
```

**Calculate order total:**
```python
from django.db.models import Sum, F
order_total = OrderItem.objects.filter(order=order_instance).aggregate(
    total=Sum(F('unit_price') * F('quantity'))
)['total']
```

## Advantages of This Approach

1. **Complete Order Lifecycle**: Full tracking from placement to delivery
2. **Role-Based Access Control**: Different permissions for consumers and chefs
3. **Flexible Pricing**: Unit prices stored at order time to handle menu price changes
4. **Special Requests Handling**: Accommodate specific customer requirements
5. **Real-time Tracking**: Customers can track their orders in real-time
6. **Data Integrity**: Foreign key constraints ensure order consistency

## Testing

```bash
# Run orders-specific tests
python manage.py test orders

# Shell testing
python manage.py shell
>>> from orders.models import Order, OrderItem
>>> from dishes.models import Dish
>>> from authentication.models import User
>>> 
>>> # Get a consumer and a chef
>>> consumer = User.objects.get(consumer__isnull=False).first()
>>> chef = User.objects.get(chef__isnull=False).first()
>>> 
>>> # Get a dish from the chef
>>> dish = Dish.objects.filter(chef=chef).first()
>>> 
>>> # Create an order
>>> order = Order.objects.create(
...     customer=consumer,
...     chef=chef,
...     total_amount=dish.price,
...     delivery_address="123 Main St, City, Country",
...     delivery_longitude=31.2357,
...     delivery_latitude=30.0444
... )
>>> 
>>> # Add an order item
>>> order_item = OrderItem.objects.create(
...     order=order,
...     dish=dish,
...     quantity=2,
...     unit_price=dish.price
... )
>>> 
>>> # Update order status
>>> order.status = 'confirmed'
>>> order.save()
>>> 
>>> # Get order total
>>> order_total = sum(item.get_subtotal() for item in order.items.all())
>>> print(f"Order total: {order_total}")
```