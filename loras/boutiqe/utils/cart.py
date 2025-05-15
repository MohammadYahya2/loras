from django.contrib.auth.models import User
from ..models import Cart, CartItem, Wishlist, ContactInfo
from django.db.utils import OperationalError, IntegrityError
from django.db.models import Sum, F, Q
from django.contrib import messages
from django.db.models.functions import Coalesce
from django.utils import timezone
from django.urls import reverse
from decimal import Decimal

def get_or_create_cart(request):
    """
    Get or create a cart for the current user or session.
    
    For authenticated users, get or create a cart linked to their account.
    For anonymous users, get or create a cart linked to their session key.
    """
    try:
        if request.user.is_authenticated:
            # For authenticated users
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={'session_key': None}
            )
        else:
            # For anonymous users
            if not request.session.session_key:
                request.session.save()  # Ensure we have a session key
                
            session_key = request.session.session_key
            try:
                cart, created = Cart.objects.get_or_create(
                    session_key=session_key,
                    defaults={'user': None}
                )
            except OperationalError:
                # If session_key field doesn't exist yet, create a temporary cart
                # This will be replaced once migrations are applied
                cart = Cart(user=None)
    except Exception:
        # Fallback to a temporary cart
        cart = Cart(user=None)
    
    return cart

def get_cart_or_error(request):
    """
    Get cart items and cart object for the current user or session.
    Returns a tuple of (cart_items, cart)
    """
    from ..models import CartItem, Cart
    
    if request.user.is_authenticated:
        cart_items = CartItem.objects.filter(user=request.user)
        try:
            cart = Cart.objects.get(user=request.user)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(user=request.user)
    else:
        # For guest users
        session_key = request.session.session_key
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        
        cart_items = CartItem.objects.filter(session_key=session_key)
        try:
            cart = Cart.objects.get(session_key=session_key)
        except Cart.DoesNotExist:
            cart = Cart.objects.create(session_key=session_key)
    
    return cart_items, cart

def get_cart_item_count(request):
    """
    Get the total number of items in the user's cart.
    For anonymous users, get the count based on the session key.
    """
    try:
        cart = get_or_create_cart(request)
        return cart.items.count()
    except Exception:
        return 0

def get_cart_items_total_quantity(request):
    """
    Get the total quantity of all items in the cart (counting multiples of the same item).
    """
    try:
        cart = get_or_create_cart(request)
        result = cart.items.aggregate(total_quantity=Sum('quantity'))
        return result['total_quantity'] or 0
    except Exception:
        return 0

def check_cart_limit(request):
    """
    Check if the cart has reached the maximum allowed quantity (30 items).
    Returns True if the limit has been reached, False otherwise.
    """
    total_quantity = get_cart_items_total_quantity(request)
    return total_quantity >= 30

def move_session_cart_to_user(request):
    """
    Move items from a session-based cart to a user's cart after login.
    This should be called when a user logs in.
    """
    if not request.user.is_authenticated or not request.session.session_key:
        return
    
    try:
        # Get the session cart if it exists
        try:
            session_cart = Cart.objects.get(
                session_key=request.session.session_key,
                user__isnull=True
            )
        except (Cart.DoesNotExist, OperationalError):
            return
        
        # Get or create the user's cart
        user_cart, created = Cart.objects.get_or_create(
            user=request.user,
            defaults={'session_key': None}
        )
        
        # Move all items from session cart to user cart
        for item in session_cart.items.all():
            # Check if the same product with same attributes exists in the user cart
            existing_item = user_cart.items.filter(
                product=item.product,
                color=item.color,
                size=item.size
            ).first()
            
            if existing_item:
                # If the item already exists, just update the quantity
                existing_item.quantity += item.quantity
                # Ensure we don't exceed the maximum quantity per cart
                if existing_item.quantity > 30:
                    existing_item.quantity = 30
                existing_item.save()
            else:
                # Move the item to the user's cart
                item.cart = user_cart
                item.user = request.user
                item.save()
        
        # Delete the now-empty session cart
        session_cart.delete()
        
        # Move wishlist items as well
        merge_session_wishlist_to_user(request)
        
        # Move contact info if any
        merge_session_contact_to_user(request)
    except Exception as e:
        # Log the error but don't break user experience
        print(f"Error merging carts: {e}")

def merge_session_wishlist_to_user(request):
    """
    Move wishlist items from session to user after login.
    """
    if not request.user.is_authenticated or not request.session.session_key:
        return
    
    try:
        # Get all session wishlist items
        try:
            session_wishlist_items = Wishlist.objects.filter(
                session_key=request.session.session_key,
                user__isnull=True
            )
        except OperationalError:
            # If session_key field doesn't exist yet, return
            return
        
        # For each item, add it to the user's wishlist if not already there
        for item in session_wishlist_items:
            user_has_item = Wishlist.objects.filter(
                user=request.user,
                product=item.product
            ).exists()
            
            if not user_has_item:
                # Create a new wishlist item for the user
                Wishlist.objects.create(
                    user=request.user,
                    product=item.product
                )
        
        # Delete all session wishlist items
        session_wishlist_items.delete()
    except Exception as e:
        # Log the error but don't break user experience
        print(f"Error merging wishlists: {e}")

def merge_session_contact_to_user(request):
    """
    Move contact information from session to user after login.
    """
    if not request.user.is_authenticated or not request.session.session_key:
        return
    
    try:
        # Get all session contact info
        session_contacts = ContactInfo.objects.filter(
            session_key=request.session.session_key,
            user__isnull=True
        )
        
        # For each contact, add it to the user if not already there
        for contact in session_contacts:
            # Check if user already has contact with this phone number
            user_has_contact = ContactInfo.objects.filter(
                user=request.user,
                phone=contact.phone
            ).exists()
            
            if not user_has_contact:
                # Create new contact for the user
                ContactInfo.objects.create(
                    user=request.user,
                    name=contact.name,
                    phone=contact.phone,
                    address=contact.address,
                    city=contact.city,
                    note=contact.note
                )
        
        # Update any orders linked to the session to be linked to the user
        from ..models import Order
        orders = Order.objects.filter(
            session_key=request.session.session_key,
            user__isnull=True
        )
        for order in orders:
            order.user = request.user
            order.save()
            
        # Delete all session contacts
        session_contacts.delete()
    except Exception as e:
        # Log the error but don't break user experience
        print(f"Error merging contact info: {e}")

def save_contact_info(request, name, phone, address, city=None, note=None):
    """
    Save contact information for guest or user.
    Returns the created/updated ContactInfo object.
    """
    try:
        if request.user.is_authenticated:
            # For authenticated users
            contact, created = ContactInfo.objects.get_or_create(
                user=request.user,
                phone=phone,
                defaults={
                    'name': name,
                    'address': address,
                    'city': city,
                    'note': note,
                    'session_key': None
                }
            )
            # Update existing contact info if it already exists
            if not created:
                contact.name = name
                contact.address = address
                if city:
                    contact.city = city
                if note:
                    contact.note = note
                contact.save()
        else:
            # For guest users
            if not request.session.session_key:
                request.session.save()
                
            session_key = request.session.session_key
            contact, created = ContactInfo.objects.get_or_create(
                session_key=session_key,
                phone=phone,
                defaults={
                    'name': name, 
                    'address': address,
                    'city': city,
                    'note': note,
                    'user': None
                }
            )
            # Update existing contact info if it already exists
            if not created:
                contact.name = name
                contact.address = address
                if city:
                    contact.city = city
                if note:
                    contact.note = note
                contact.save()
        
        return contact
    except Exception as e:
        print(f"Error saving contact info: {e}")
        return None 