from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from .models import UserProfile

User = get_user_model()

class UserProfileBackend(ModelBackend):
    """
    Custom authentication backend that checks both User.is_active and UserProfile.is_active
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return None
        
        # Check password first
        if user.check_password(password):
            # Check if User is active
            if not user.is_active:
                return None
            
            # Check if UserProfile exists and is active
            try:
                user_profile = UserProfile.objects.get(user=user)
                if not user_profile.is_active:
                    return None
            except UserProfile.DoesNotExist:
                # If no UserProfile exists, allow login (for backward compatibility)
                pass
            
            return user
        return None
    
    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
            
            # Check if User is active
            if not user.is_active:
                return None
            
            # Check if UserProfile exists and is active
            try:
                user_profile = UserProfile.objects.get(user=user)
                if not user_profile.is_active:
                    return None
            except UserProfile.DoesNotExist:
                # If no UserProfile exists, allow user (for backward compatibility)
                pass
            
            return user
        except User.DoesNotExist:
            return None
