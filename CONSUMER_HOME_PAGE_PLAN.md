# Consumer Home Page Implementation Plan

## Overview
This document outlines the plan for implementing the consumer home page that will be displayed after a consumer logs in. The home page will include several key sections: categories, search functionality, top-rated chefs, and top-rated dishes.

## Page Structure
After successful consumer login, the frontend will redirect the user to the home page with the following layout:

```
┌─────────────────────────────────────────┐
│              Navigation Bar             │
├─────────────────────────────────────────┤
│                Search Bar               │
├─────────────────────────────────────────┤
│              Categories Section         │
├─────────────────────────────────────────┤
│              Top Rated Chefs            │
├─────────────────────────────────────────┤
│              Top Rated Dishes           │
└─────────────────────────────────────────┘
```

## Components Breakdown

### 1. Category Section
- **Purpose**: Display available food categories for easy navigation
- **Backend Endpoint**: `GET /api/dishes/categories/`
- **Display**: Grid or horizontal scroll of category cards with icons/images
- **Interaction**: Clicking a category navigates to the dishes list filtered by that category

### 2. Search Field
- **Purpose**: Allow consumers to search for dishes and chefs
- **Backend Endpoints**:
  - For dishes: `GET /api/dishes/?search={query}`
  - For chefs: Custom endpoint to search chef profiles
- **Features**:
  - Real-time suggestions as the user types
  - Ability to filter search results by category, price range, etc.
  - Visual indication of search results count

### 3. Top Rated Chefs Section
- **Purpose**: Showcase highly-rated chefs to encourage discovery
- **Backend Endpoint**: `GET /api/auth/chefs/top-rated/` (may require new endpoint)
- **Display Criteria**:
  - Sorted by average rating (descending)
  - Limited to top 5-10 chefs
  - Include chef name, rating, specialty, and profile picture
- **Additional Info**: Number of orders, delivery time, and cuisine types

### 4. Top Rated Dishes Section
- **Purpose**: Highlight popular and highly-rated dishes
- **Backend Endpoint**: `GET /api/dishes/?sort=rating&limit=10` (may require new endpoint)
- **Display Criteria**:
  - Sorted by average rating and number of reviews
  - Include dish name, rating, price, chef info, and image
  - Show number of reviews and brief description

## Backend API Requirements

### New Endpoints Needed
1. **Top Rated Chefs**: `GET /api/auth/chefs/top-rated/`
   - Returns chefs ordered by average rating
   - Includes relevant chef information for display

2. **Search Endpoint**: `GET /api/search/?q={query}&type={dish|chef|both}`
   - Unified search endpoint for dishes and/or chefs
   - Returns combined or filtered results based on type parameter

3. **Enhanced Dish Endpoint**: `GET /api/dishes/?sort=rating&limit=10`
   - Return dishes sorted by rating with additional filtering options

### Existing Endpoints to Utilize
1. **Categories**: `GET /api/dishes/categories/`
2. **Dish List**: `GET /api/dishes/`
3. **Dish Detail**: `GET /api/dishes/{id}/`
4. **Chef Detail**: `GET /api/auth/profile/{chef_id}/`

## Frontend Implementation

### Routing
- After successful login, redirect consumer to `/home` route
- Implement protected route to ensure only authenticated consumers can access

### Component Structure
```
HomePage/
├── SearchBar/
├── CategorySection/
├── TopRatedChefs/
├── TopRatedDishes/
└── Navigation/
```

### State Management
- Store search results in component state
- Cache category data to prevent repeated API calls
- Implement loading states for better UX

### Responsive Design
- Mobile-first approach
- Grid layout adjusts based on screen size
- Touch-friendly elements for mobile users

## User Flow

1. Consumer logs in successfully
2. Frontend redirects to home page
3. Page loads with:
   - Category section populated
   - Top rated chefs displayed
   - Top rated dishes displayed
4. Consumer can:
   - Browse categories
   - Search for dishes/chefs
   - View details of top-rated items
   - Navigate to other sections of the app

## Technical Considerations

### Performance
- Implement pagination for large datasets
- Use lazy loading for images
- Cache API responses where appropriate
- Debounce search input to limit API calls

### Error Handling
- Handle API failures gracefully
- Show user-friendly error messages
- Implement retry mechanisms for failed requests

### Security
- Ensure all API calls are authenticated where required
- Sanitize search inputs to prevent injection attacks
- Validate all data before displaying

## Future Enhancements
- Personalized recommendations based on order history
- Location-based chef suggestions
- Featured promotions section
- Recently viewed items carousel
- Dietary preference filters

## Timeline
- Phase 1: Implement basic page structure and routing (1 day)
- Phase 2: Integrate category section and search functionality (2 days)
- Phase 3: Implement top-rated chefs and dishes sections (2 days)
- Phase 4: Add responsive design and polish UI (1 day)
- Phase 5: Testing and bug fixes (1 day)