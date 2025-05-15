# Guest checkout upgrade 2025/05/13
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.sessions.middleware import SessionMiddleware

from boutiqe.models import (
    Product, Category, Cart, CartItem, Wishlist, 
    Color, Size, Order, OrderItem, ContactInfo
)
import json

class GuestCheckoutTestCase(TestCase):
    """Test the guest checkout functionality."""
    
    def setUp(self):
        # Create a test category
        self.category = Category.objects.create(name="اختبار", slug="test")
        
        # Create test products
        self.product1 = Product.objects.create(
            name="منتج اختبار 1",
            slug="test-product-1",
            description="وصف المنتج الأول",
            price=100.00,
            category=self.category,
            in_stock=True
        )
        
        self.product2 = Product.objects.create(
            name="منتج اختبار 2",
            slug="test-product-2",
            description="وصف المنتج الثاني",
            price=200.00,
            category=self.category,
            in_stock=True
        )
        
        # Create some colors and sizes
        self.color1 = Color.objects.create(name="أحمر", code="#FF0000")
        self.color2 = Color.objects.create(name="أزرق", code="#0000FF")
        self.size1 = Size.objects.create(name="S")
        self.size2 = Size.objects.create(name="M")
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        # Setup client
        self.client = Client()
    
    def test_guest_checkout_flow(self):
        """Test the complete guest checkout flow."""
        # Add products to cart
        response = self.client.post(
            reverse('boutiqe:add_to_cart'),
            data=json.dumps({
                'product_id': self.product1.id,
                'quantity': 2,
                'color_id': self.color1.id,
                'size_id': self.size1.id
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {
            'success': True,
            'message': 'تمت إضافة المنتج إلى سلة التسوق',
            'cart_count': 2
        })
        
        # Add another product to cart
        response = self.client.post(
            reverse('boutiqe:add_to_cart'),
            data=json.dumps({
                'product_id': self.product2.id,
                'quantity': 1
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        # Add product to wishlist
        response = self.client.get(
            reverse('boutiqe:add_to_wishlist', args=[self.product2.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        
        # Get session key
        session_key = self.client.session.session_key
        self.assertIsNotNone(session_key)
        
        # Check cart contents
        cart = Cart.objects.get(session_key=session_key)
        self.assertEqual(cart.items.count(), 2)
        
        # Check wishlist contents
        wishlist_items = Wishlist.objects.filter(session_key=session_key)
        self.assertEqual(wishlist_items.count(), 1)
        
        # Complete checkout
        response = self.client.post(
            reverse('boutiqe:checkout'),
            {
                'name': 'عميل اختبار',
                'phone': '1234567890',
                'address': 'عنوان اختبار',
                'city': 'مدينة اختبار',
                'note': 'ملاحظة اختبار'
            }
        )
        
        # Check redirect to confirmation page
        self.assertRedirects(response, reverse('boutiqe:order_confirmation'))
        
        # Check order was created
        order = Order.objects.filter(session_key=session_key).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.items.count(), 2)
        self.assertEqual(order.contact_info.name, 'عميل اختبار')
        
        # Check cart was emptied
        self.assertEqual(cart.items.count(), 0)
        
        # Wishlist should still exist
        self.assertEqual(Wishlist.objects.filter(session_key=session_key).count(), 1)
    
    def test_merge_cart_wishlist_after_login(self):
        """Test merging guest cart and wishlist with user account after login."""
        # Add product to cart as guest
        response = self.client.post(
            reverse('boutiqe:add_to_cart'),
            data=json.dumps({
                'product_id': self.product1.id,
                'quantity': 2
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Add product to wishlist as guest
        response = self.client.get(
            reverse('boutiqe:add_to_wishlist', args=[self.product2.id]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        # Get session key
        session_key = self.client.session.session_key
        
        # Login
        self.client.login(username='testuser', password='testpassword')
        
        # Check that cart and wishlist were merged
        user_cart = Cart.objects.get(user=self.user)
        self.assertEqual(user_cart.items.count(), 1)
        self.assertEqual(user_cart.items.first().product, self.product1)
        
        user_wishlist = Wishlist.objects.filter(user=self.user)
        self.assertEqual(user_wishlist.count(), 1)
        self.assertEqual(user_wishlist.first().product, self.product2)
        
        # Check that guest cart and wishlist were removed
        self.assertEqual(Cart.objects.filter(session_key=session_key).count(), 0)
        self.assertEqual(Wishlist.objects.filter(session_key=session_key).count(), 0)
    
    def test_cart_limit(self):
        """Test that cart is limited to 30 items."""
        # Add 30 items to cart
        response = self.client.post(
            reverse('boutiqe:add_to_cart'),
            data=json.dumps({
                'product_id': self.product1.id,
                'quantity': 30
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content.decode(), {
            'success': True,
            'message': 'تمت إضافة المنتج إلى سلة التسوق',
            'cart_count': 30
        })
        
        # Try to add one more
        response = self.client.post(
            reverse('boutiqe:add_to_cart'),
            data=json.dumps({
                'product_id': self.product2.id,
                'quantity': 1
            }),
            content_type='application/json',
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content.decode())
        self.assertFalse(response_data['success'])
        self.assertEqual(response_data['cart_count'], 30)
    
    def test_session_key_uniqueness(self):
        """Test that session key uniqueness constraint is enforced."""
        # Create a cart with a session key
        session_key = "test_session_key"
        cart1 = Cart.objects.create(session_key=session_key)
        
        # Try to create another cart with the same session key
        with self.assertRaises(Exception):
            Cart.objects.create(session_key=session_key)
        
        # Try to create a cart with both user and session key
        with self.assertRaises(Exception):
            Cart.objects.create(user=self.user, session_key=session_key) 