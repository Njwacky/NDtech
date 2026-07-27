"""
Main Views Module - Imports from modular view files
"""
# Import all views from the 3 modular files
from .views_core import *
from .views_pos import *
from .views_communications import *

# This file serves as the main entry point for URL routing
# All view functions are now organized into:
# - views_core.py: Authentication, User management, Dashboard
# - views_pos.py: POS system, Sales, Orders, Inventory
# - views_communications.py: Notifications, FCM, Airtime, Tracking

print("Views loaded from modular files:")
print("- views_core.py: Authentication, Users, Dashboard")
print("- views_pos.py: POS, Sales, Orders, Inventory")
print("- views_communications.py: Notifications, FCM, Airtime, Tracking")
