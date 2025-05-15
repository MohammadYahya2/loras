from django import template
from django.conf import settings
from boutiqe.models import Wishlist
from django.template.defaultfilters import floatformat

register = template.Library()

@register.filter
def map_product(wishlist_items):
    """
    Returns a list of products from a wishlist queryset
    """
    return [item.product for item in wishlist_items]

@register.filter
def is_in_wishlist(product, user):
    """
    Check if a product is in the user's wishlist
    """
    if user.is_authenticated:
        return product.wishlist_set.filter(user=user).exists()
    return False

@register.filter
def sub(value, arg):
    """
    Subtracts the arg from the value.
    """
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        try:
            return value - arg
        except Exception:
            return 0

@register.filter
def percentage(value, max_value):
    """Calculate what percentage the value is of max_value."""
    try:
        value = float(value)
        max_value = float(max_value)
        if max_value <= 0:
            return 0
        return (value / max_value) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply the arg with the value."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0 