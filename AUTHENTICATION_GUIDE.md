# Authentication Refactor: Chef vs Consumer User Types

## Overview
The authentication system now uses **model inheritance** to cleanly separate Chef and Consumer user profiles while maintaining shared common attributes.

### Architecture

```
User (abstract base with common fields)
├── Chef (OneToOne to User, chef-specific fields)
└── Consumer (OneToOne to User, consumer-specific fields)
```

## Database Changes

Run migrations to create the new `Chef` and `Consumer` tables:

```bash
python manage.py makemigrations authentication
python manage.py migrate
```

## Breaking Changes from Previous Version

### Old Schema
- Single `User` model with `is_chef` boolean flag

### New Schema
- `User` model (no `is_chef` field)
- `Chef` model with `OneToOneField` to `User`
- `Consumer` model with `OneToOneField` to `User`

**Data Migration (if existing users):**
If you have existing users, you'll need a data migration to create Chef/Consumer profiles. Run:

```bash
python manage.py makemigrations authentication --empty create_initial_profiles --name
```

Then manually populate Chef/Consumer objects based on your migration logic.

## Signup Endpoint Changes

### Request Payload
```json
{
  "first_name": "Alice",
  "last_name": "Chef",
  "email": "alice@example.com",
  "phone_number": "+201234567890",
  "password": "secure-password",
  "address_longitude": 31.2357,
  "address_latitude": 30.0444,
  "user_type": "chef",
  "bio": "Passionate about Italian cuisine",
  "cuisine_specialties": "Italian, Mediterranean",
  "years_of_experience": 5
}
```

**For Consumer:**
```json
{
  "first_name": "Bob",
  "last_name": "Consumer",
  "email": "bob@example.com",
  "phone_number": "+201234567891",
  "password": "secure-password",
  "address_longitude": 31.2357,
  "address_latitude": 30.0444,
  "user_type": "consumer",
  "dietary_preferences": "vegan",
  "allergies": "nuts, shellfish"
}
```

### Response
Returns the full Chef or Consumer profile (includes nested User data).

## Login Response Changes

Login now includes a `profile` field with type-specific data:

```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "alice@example.com",
    "first_name": "Alice",
    "last_name": "Chef",
    "user_type": "chef"
  },
  "profile": {
    "id": 1,
    "user": {...},
    "rating": 0.0,
    "total_reviews": 0,
    "bio": "Passionate about Italian cuisine",
    "cuisine_specialties": "Italian, Mediterranean",
    "years_of_experience": 5,
    "is_verified": false
  }
}
```

## Admin Interface

- **Users**: View all users, filter by `is_active`, `is_staff`, `created_at`
- **Chefs**: Dedicated table showing chef-specific info (rating, verification, experience)
- **Consumers**: Dedicated table showing consumer-specific info (dietary preferences, order count)
- **Payment Cards**: Track payment methods per user

## Best Practices

### Querying

**Get user type:**
```python
user.get_user_type()  # Returns 'chef' or 'consumer'
```

**Get Chef profile:**
```python
chef = user.chef  # OneToOne access
# or
chef = Chef.objects.get(user=user)
```

**Get Consumer profile:**
```python
consumer = user.consumer  # OneToOne access
# or
consumer = Consumer.objects.get(user=user)
```

**Filter by type:**
```python
chefs = Chef.objects.all()  # All chefs
consumers = Consumer.objects.all()  # All consumers
```

### Adding Chef-Specific Fields

Simply extend the `Chef` model:

```python
class Chef(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='chef')
    # ... existing fields
    new_field = models.CharField(max_length=100)  # Add your field
```

Then run migrations.

### Adding Relations to Chef/Consumer

**Example: Chef can have many Menus**
```python
class Menu(models.Model):
    chef = models.ForeignKey(Chef, on_delete=models.CASCADE, related_name='menus')
    title = models.CharField(max_length=100)
    # ...
```

**Example: Consumer can have many Orders**
```python
class Order(models.Model):
    consumer = models.ForeignKey(Consumer, on_delete=models.CASCADE, related_name='orders')
    chef = models.ForeignKey(Chef, on_delete=models.SET_NULL, null=True)
    # ...
```

## Advantages of This Approach

1. **Clean Separation**: Chef and Consumer schemas don't leak into each other
2. **Scalability**: Easy to add Chef/Consumer-specific features later
3. **Relational Integrity**: Use ForeignKey directly to Chef/Consumer, not User
4. **Admin Interface**: Separate admin pages for each type
5. **Query Efficiency**: `Chef.objects.filter(...)` only queries chef data
6. **Future-Proof**: Can add more user types (Admin, Support, etc.) without changing User model

## Testing

```bash
# Create superuser (still required for admin access)
python manage.py createsuperuser

# Run tests
python manage.py test authentication

# Shell testing
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from authentication.models import Chef, Consumer
>>> User = get_user_model()
>>> chef = Chef.objects.first()
>>> chef.user.email  # Access user from chef
>>> chef.user.get_user_type()  # Should return 'chef'
```
