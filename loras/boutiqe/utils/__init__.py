# Utils package
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from .cart import move_session_cart_to_user

# Register signal to move session cart to user cart on login
@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    """Handle merging carts when a user logs in"""
    try:
        move_session_cart_to_user(request)
    except Exception as e:
        # Log the error but don't break the login process
        print(f"Error merging carts: {str(e)}") 