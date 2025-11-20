from django.apps import AppConfig

class FoodOrderingConfig(AppConfig):
    default_auto_field = 'food_ordering'
    name = 'Food Ordering System'
    verbose_name = 'Food Ordering'
    
    def ready(self):
        """Check if the food ordering system is ready"""
        return True
