from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from food_ordering.models import Restaurant, MenuCategory, MenuItem, DeliveryZone
import random
import string

class Command(BaseCommand):
    help = 'Sets up a sample restaurant with menu items for testing the food ordering system'
    
    def handle(self, *args, **options):
        # Get or create a superuser
        username = options.get('username', 'admin')
        email = options.get('email', 'admin@example.com')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password='admin123'
            )
            self.stdout.write(f'Created superuser: {username}')
        
        # Create sample restaurant
        restaurant = Restaurant.objects.create(
            owner=user,
            name='Sample Restaurant',
            description='A sample restaurant for testing the food ordering system',
            phone='0123456789',
            email='restaurant@example.com',
            address='123 Sample Street, Johannesburg, Gauteng',
            latitude=-26.2041,
            longitude=28.0473,
            commission_rate=0.15,
            delivery_time_minutes=30,
            min_order_amount=50.00
        )
        
        self.stdout.write(f'Created restaurant: {restaurant.name}')
        
        # Create delivery zones
        delivery_zones = [
            DeliveryZone.objects.create(
                restaurant=restaurant,
                name='Central Johannesburg',
                base_fee=15.00,
                per_km_fee=2.50,
                coordinates=[{"lat": -26.2041, "lng": 28.0473}, {"lat": -26.1951, "lng": 28.0553}],
                center_latitude=-26.2000,
                center_longitude=28.0500,
                estimated_time_minutes=25
            ),
            DeliveryZone.objects.create(
                restaurant=restaurant,
                name='Northern Suburbs',
                base_fee=20.00,
                per_km_fee=3.00,
                coordinates=[{"lat": -26.1500, "lng": 28.1000}, {"lat": -26.1400, "lng": 28.0900}],
                center_latitude=-26.1450,
                center_longitude=28.0950,
                estimated_time_minutes=35
            ),
            DeliveryZone.objects.create(
                restaurant=restaurant,
                name='Eastern Johannesburg',
                base_fee=25.00,
                per_km_fee=3.50,
                coordinates=[{"lat": -26.1200, "lng": 28.1800}, {"lat": -26.1100, "lng": 28.1600}],
                center_latitude=-26.1150,
                center_longitude=28.1400,
                estimated_time_minutes=40
            )
        ]
        
        # Create operating hours
        operating_hours = {
            'monday': {'open': '08:00', 'close': '22:00'},
            'tuesday': {'open': '08:00', 'close': '22:00'},
            'wednesday': {'open': '08:00', 'close': '22:00'},
            'thursday': {'open': '08:00', 'close': '22:00'},
            'friday': {'open': '08:00', 'close': '23:00'},
            'saturday': {'open': '09:00', 'close': '23:00'},
            'sunday': {'open': '09:00', 'close': '21:00'}
        }
        
        restaurant.operating_hours = operating_hours
        
        # Create menu categories
        categories = [
            MenuCategory.objects.create(
                restaurant=restaurant,
                name='Burgers',
                description='Various types of burgers',
                display_order=1
            ),
            MenuCategory.objects.create(
                restaurant=restaurant,
                name='Sides & Extras',
                description='French fries, onion rings, and other side items',
                display_order=2
            ),
            MenuCategory.objects.create(
                restaurant=restaurant,
                name='Beverages',
                description='Soft drinks, juices, and other beverages',
                display_order=3
            ),
            MenuCategory.objects.create(
                restaurant=restaurant,
                name='Desserts',
                description='Sweet treats and desserts',
                display_order=4
            ),
            MenuCategory.objects.create(
                restaurant=restaurant,
                name='Breakfast',
                description='Breakfast items and morning meals',
                display_order=5
            )
        ]
        
        self.stdout.write(f'Created {len(categories)} menu categories')
        
        # Create sample menu items
        menu_items = [
            # Burgers
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[0],
                name='Classic Beef Burger',
                description='Juicy beef patty with lettuce, tomato, onion, and special sauce',
                price=45.00,
                preparation_time=15,
                spice_level='medium',
                is_available=True
            ),
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[0],
                name='Cheese Burger',
                description='Beef patty with extra cheese, lettuce, tomato, and onion',
                price=50.00,
                preparation_time=18,
                spice_level='medium',
                is_available=True
            ),
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[0],
                name='Chicken Burger',
                description='Crispy chicken breast with lettuce, tomato, and mayo',
                price=42.00,
                preparation_time=12,
                spice_level='mild',
                is_available=True
            ),
            
            # Sides
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[1],
                name='French Fries',
                description='Crispy golden french fries with sea salt',
                price=25.00,
                preparation_time=8,
                is_available=True
            ),
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[1],
                name='Onion Rings',
                description='Crispy breaded onion rings',
                price=15.00,
                preparation_time=5,
                is_available=True
            ),
            
            # Beverages
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[2],
                name='Coca-Cola',
                description='Classic Coca-Cola 500ml',
                price=18.00,
                preparation_time=2,
                is_available=True
            ),
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[2],
                name='Orange Juice',
                description='Freshly squeezed orange juice',
                price=20.00,
                preparation_time=3,
                is_available=True
            ),
            
            # Desserts
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[3],
                name='Chocolate Cake',
                description='Rich chocolate cake with chocolate frosting',
                price=35.00,
                preparation_time=10,
                spice_level='mild',
                is_available=True
            ),
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[3],
                name='Pancakes',
                description='Fluffy buttermilk pancakes with maple syrup',
                price=28.00,
                preparation_time=15,
                spice_level='mild',
                is_available=True
            ),
            
            # Breakfast
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[4],
                name='Eggs & Bacon',
                description='Two eggs cooked to order with crispy bacon',
                price=55.00,
                preparation_time=12,
                spice_level='medium',
                is_available=True
            ),
            MenuItem.objects.create(
                restaurant=restaurant,
                category=categories[4],
                name='Coffee',
                description='Freshly brewed coffee',
                price=18.00,
                preparation_time=3,
                spice_level='mild',
                is_available=True
            )
        ]
        
        self.stdout.write(f'Created {len(menu_items)} menu items')
        
        # Mark some items as unavailable for testing
        menu_items[5].is_available = False  # Cheese Burger temporarily unavailable
        
        # Update order counts for popularity tracking
        for item in menu_items[1:3]:  # Burgers
            item.order_count = random.randint(10, 100)
            item.save()
        
        self.stdout.write('Updated item popularity for testing')
        
        self.stdout.write(self.style.SUCCESS('Sample restaurant setup completed!'))
        self.stdout.write('')
        self.stdout.write('Restaurant Details:')
        self.stdout.write(f'  Name: {restaurant.name}')
        self.stdout.write(f'  ID: {restaurant.id}')
        self.stdout.write(f'  Owner: {restaurant.owner.username}')
        self.stdout.write(f'  Phone: {restaurant.phone}')
        self.stdout.write('')
        self.stdout.write('Menu Categories Created')
