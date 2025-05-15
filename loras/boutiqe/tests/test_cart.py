from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from boutiqe.models import Product, Category, Cart, CartItem, Wishlist
from boutiqe.utils.cart import get_or_create_cart, move_session_cart_to_user

class CartSessionTestCase(TestCase):
    """Test session-based cart functionality."""
    
    def setUp(self):
        """Set up test data."""
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Create a test category
        self.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        
        # Create test products
        self.product1 = Product.objects.create(
            name='Test Product 1',
            slug='test-product-1',
            description='Test description 1',
            price=100.00,
            category=self.category,
            in_stock=True
        )
        
        self.product2 = Product.objects.create(
            name='Test Product 2',
            slug='test-product-2',
            description='Test description 2',
            price=200.00,
            category=self.category,
            in_stock=True
        )
        
        # Set up client
        self.client = Client()
    
    def test_anonymous_user_cart_creation(self):
        """Test that anonymous users can create a cart with a session."""
        # Make a request to add an item to the cart
        response = self.client.post(
            reverse('boutiqe:add_to_cart'),
            data={'product_id': self.product1.id, 'quantity': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        
        # Check that a cart was created with a session key
        self.assertEqual(Cart.objects.count(), 1)
        cart = Cart.objects.first()
        self.assertIsNone(cart.user)
        self.assertIsNotNone(cart.session_key)
        
        # Check that the item was added to the cart
        self.assertEqual(cart.items.count(), 1)
        cart_item = cart.items.first()
        self.assertEqual(cart_item.product, self.product1)
        self.assertEqual(cart_item.quantity, 2)
    
    def test_merge_session_cart_to_user(self):
        """Test that session cart items are merged to user cart on login."""
        # First add items to a session cart
        self.client.post(
            reverse('boutiqe:add_to_cart'),
            data={'product_id': self.product1.id, 'quantity': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Check that the cart was created
        self.assertEqual(Cart.objects.count(), 1)
        session_cart = Cart.objects.first()
        self.assertIsNone(session_cart.user)
        
        # Now log in the user
        self.client.login(username='testuser', password='testpassword123')
        
        # Add another product to the cart
        self.client.post(
            reverse('boutiqe:add_to_cart'),
            data={'product_id': self.product2.id, 'quantity': 1},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Check that the carts were merged
        self.assertEqual(Cart.objects.count(), 1)
        user_cart = Cart.objects.first()
        self.assertEqual(user_cart.user, self.user)
        self.assertEqual(user_cart.items.count(), 2)
        
        # Check the items in the cart
        items = user_cart.items.all()
        item_products = [item.product for item in items]
        self.assertIn(self.product1, item_products)
        self.assertIn(self.product2, item_products)
    
    def test_unique_constraint_enforcement(self):
        """Test that the unique constraints are enforced."""
        # Create a cart with a user
        user_cart = Cart.objects.create(user=self.user)
        
        # Try to create another cart with the same user
        with self.assertRaises(Exception):
            Cart.objects.create(user=self.user)
        
        # Create a cart with just a session key
        session_key = 'test_session_key'
        session_cart = Cart.objects.create(session_key=session_key)
        
        # Try to create another cart with the same session key
        with self.assertRaises(Exception):
            Cart.objects.create(session_key=session_key)
    
    def test_add_to_wishlist_session(self):
        """Test that anonymous users can add to wishlist."""
        # Add to wishlist
        response = self.client.get(
            reverse('boutiqe:add_to_wishlist', args=[self.product1.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        
        # Check that a wishlist item was created
        self.assertEqual(Wishlist.objects.count(), 1)
        wishlist_item = Wishlist.objects.first()
        self.assertIsNone(wishlist_item.user)
        self.assertIsNotNone(wishlist_item.session_key)
        self.assertEqual(wishlist_item.product, self.product1)
    
    def test_guest_checkout_workflow(self):
        """Test the complete guest checkout workflow."""
        # Add items to cart
        self.client.post(
            reverse('boutiqe:add_to_cart'),
            data={'product_id': self.product1.id, 'quantity': 2},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Go to checkout
        response = self.client.get(reverse('boutiqe:checkout'))
        self.assertEqual(response.status_code, 200)
        
        # Complete checkout (simulate form submission)
        # This would be expanded with actual form data in a real test
        # but is simplified here
        pass

# --- Guest checkout upgrade 2025/05/12 --- 