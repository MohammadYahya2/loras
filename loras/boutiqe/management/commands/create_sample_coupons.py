import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from boutiqe.models import Coupon

class Command(BaseCommand):
    help = 'يقوم بإنشاء كوبونات خصم نموذجية'

    def handle(self, *args, **kwargs):
        self.stdout.write('جاري إنشاء كوبونات خصم نموذجية...')
        
        # حذف الكوبونات الموجودة (اختياري)
        if Coupon.objects.exists():
            self.stdout.write('حذف الكوبونات الموجودة...')
            Coupon.objects.all().delete()
        
        # إنشاء كوبونات نموذجية
        self.create_sample_coupons()
        
        self.stdout.write(self.style.SUCCESS('تم إنشاء الكوبونات النموذجية بنجاح!'))
    
    def create_sample_coupons(self):
        """إنشاء كوبونات نموذجية"""
        coupons_data = [
            {
                'code': 'WELCOME20',
                'discount_value': 20,
                'discount_type': 'percentage',
                'minimum_order_value': 100,
                'valid_from': timezone.now() - timedelta(days=1),
                'valid_to': timezone.now() + timedelta(days=30),
                'is_active': True,
                'max_uses': 100,
                'current_uses': 0,
            },
            {
                'code': 'FIRST50',
                'discount_value': 50,
                'discount_type': 'fixed',
                'minimum_order_value': 200,
                'valid_from': timezone.now() - timedelta(days=5),
                'valid_to': timezone.now() + timedelta(days=25),
                'is_active': True,
                'max_uses': 30,
                'current_uses': 5,
            },
            {
                'code': 'SUMMER25',
                'discount_value': 25,
                'discount_type': 'percentage',
                'minimum_order_value': 150,
                'valid_from': timezone.now() - timedelta(days=10),
                'valid_to': timezone.now() + timedelta(days=90),
                'is_active': True,
                'max_uses': 200,
                'current_uses': 50,
            },
            {
                'code': 'EXPIRED10',
                'discount_value': 10,
                'discount_type': 'percentage',
                'minimum_order_value': 0,
                'valid_from': timezone.now() - timedelta(days=60),
                'valid_to': timezone.now() - timedelta(days=30),
                'is_active': True,
                'max_uses': 100,
                'current_uses': 25,
            },
            {
                'code': 'INACTIVE15',
                'discount_value': 15,
                'discount_type': 'percentage',
                'minimum_order_value': 50,
                'valid_from': timezone.now() - timedelta(days=5),
                'valid_to': timezone.now() + timedelta(days=25),
                'is_active': False,
                'max_uses': 100,
                'current_uses': 0,
            },
            {
                'code': 'MAXUSED',
                'discount_value': 30,
                'discount_type': 'percentage',
                'minimum_order_value': 100,
                'valid_from': timezone.now() - timedelta(days=5),
                'valid_to': timezone.now() + timedelta(days=25),
                'is_active': True,
                'max_uses': 100,
                'current_uses': 100,
            },
            {
                'code': 'FREESHIP',
                'discount_value': 30,
                'discount_type': 'fixed',
                'minimum_order_value': 300,
                'valid_from': timezone.now(),
                'valid_to': timezone.now() + timedelta(days=14),
                'is_active': True,
                'max_uses': 50,
                'current_uses': 0,
            },
        ]
        
        for coupon_data in coupons_data:
            coupon = Coupon.objects.create(**coupon_data)
            self.stdout.write(f'تم إنشاء الكوبون: {coupon.code}') 