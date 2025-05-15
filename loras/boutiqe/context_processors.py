from .utils.cart import get_cart_item_count
from .models import Category, Wishlist
from django.db.utils import OperationalError

def categories_processor(request):
    """
    Add categories to context for all templates.
    """
    try:
        categories = Category.objects.all()
        return {'categories': categories}
    except:
        return {'categories': []}

def cart_item_count(request):
    """
    Add the cart item count to context for all templates.
    """
    return {'cart_item_count': get_cart_item_count(request)}

def wishlist_count(request):
    """
    Add the wishlist count to context for all templates.
    """
    count = 0
    try:
        if request.user.is_authenticated:
            count = Wishlist.objects.filter(user=request.user).count()
        elif request.session.session_key:
            # Handle case where session_key might not exist in DB yet
            try:
                count = Wishlist.objects.filter(session_key=request.session.session_key).count()
            except OperationalError:
                # If session_key column doesn't exist yet, return 0
                count = 0
    except Exception:
        # Fallback to 0 on any error
        count = 0
    
    return {'wishlist_count': count}

# --- Guest checkout upgrade 2025/05/12 --- 