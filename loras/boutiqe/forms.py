from django import forms
from .models import Product, Category, Color, Size, ProductImage, ProductVariation, TrendingCollection, Discount, Coupon

class ProductForm(forms.ModelForm):
    """Form for Product model"""
    
    colors = forms.ModelMultipleChoiceField(
        queryset=Color.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    sizes = forms.ModelMultipleChoiceField(
        queryset=Size.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Product
        fields = [
            'name', 'slug', 'description', 'price', 'discount_price', 
            'category', 'in_stock', 'is_featured', 'is_new', 'is_sale',
            'sku', 'stock_quantity', 'colors', 'sizes'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discount_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'in_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_new': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_sale': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sku': forms.TextInput(attrs={'class': 'form-control'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }
    
    def save(self, commit=True):
        instance = super().save(commit=commit)
        
        if commit:
            # Add colors to product
            if self.cleaned_data.get('colors'):
                instance.colors.set(self.cleaned_data['colors'])
            
            # Add sizes to product
            if self.cleaned_data.get('sizes'):
                instance.sizes.set(self.cleaned_data['sizes'])
                
            # Create product variations if needed
            if self.cleaned_data.get('colors') and self.cleaned_data.get('sizes'):
                # If both colors and sizes are selected, create variations for each combination
                for color in self.cleaned_data['colors']:
                    for size in self.cleaned_data['sizes']:
                        # Check if variation already exists
                        variation, created = ProductVariation.objects.get_or_create(
                            product=instance,
                            color=color,
                            size=size,
                            defaults={'stock_count': instance.stock_quantity}  # Use product stock as default
                        )
        
        return instance

class CategoryForm(forms.ModelForm):
    """Form for Category model"""
    
    class Meta:
        model = Category
        fields = ['name', 'slug', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'})
        }

class ProductImageForm(forms.ModelForm):
    """Form for ProductImage model"""
    
    class Meta:
        model = ProductImage
        fields = ['image', 'is_main']
        widgets = {
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'is_main': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

ProductImageFormSet = forms.inlineformset_factory(
    Product, 
    ProductImage,
    form=ProductImageForm,
    extra=3,
    can_delete=True
)

class ProductVariationForm(forms.ModelForm):
    """Form for ProductVariation model"""
    
    class Meta:
        model = ProductVariation
        fields = ['color', 'size', 'stock_count']
        widgets = {
            'color': forms.Select(attrs={'class': 'form-select'}),
            'size': forms.Select(attrs={'class': 'form-select'}),
            'stock_count': forms.NumberInput(attrs={'class': 'form-control'})
        }

ProductVariationFormSet = forms.inlineformset_factory(
    Product, 
    ProductVariation,
    form=ProductVariationForm,
    extra=1,
    can_delete=True
)

class TrendingCollectionForm(forms.ModelForm):
    """Form for TrendingCollection model"""
    
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = TrendingCollection
        fields = ['name', 'slug', 'description', 'image', 'products', 'order_position', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'order_position': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class DiscountForm(forms.ModelForm):
    """نموذج إضافة/تعديل الخصومات"""
    class Meta:
        model = Discount
        fields = ['name', 'description', 'discount_percent', 'start_date', 'end_date', 'products', 'categories', 'order_position', 'image', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20'}),
            'description': forms.Textarea(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'rows': 3}),
            'discount_percent': forms.NumberInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'step': '0.01'}),
            'start_date': forms.DateTimeInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'type': 'datetime-local'}),
            'products': forms.SelectMultiple(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20 h-40'}),
            'categories': forms.SelectMultiple(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20 h-40'}),
            'order_position': forms.NumberInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'min': '0'}),
            'image': forms.FileInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-primary focus:ring-primary h-5 w-5'}),
        }

class CouponForm(forms.ModelForm):
    """نموذج إضافة/تعديل كوبونات الخصم"""
    class Meta:
        model = Coupon
        fields = ['code', 'discount_value', 'discount_type', 'minimum_order_value', 'valid_from', 'valid_to', 'is_active', 'max_uses']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'placeholder': 'SUMMER2023'}),
            'discount_value': forms.NumberInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'step': '0.01'}),
            'discount_type': forms.Select(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20'}),
            'minimum_order_value': forms.NumberInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'step': '0.01'}),
            'valid_from': forms.DateTimeInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'type': 'datetime-local'}),
            'valid_to': forms.DateTimeInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'type': 'datetime-local'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'rounded border-gray-300 text-primary focus:ring-primary h-5 w-5'}),
            'max_uses': forms.NumberInput(attrs={'class': 'w-full border-gray-300 rounded-md shadow-sm focus:border-primary focus:ring focus:ring-primary focus:ring-opacity-20', 'min': '1'}),
        }
    
    def clean_code(self):
        code = self.cleaned_data['code']
        # تحويل الكود إلى كبتل (Uppercase) وإزالة المسافات
        return code.upper().strip()
    
    def clean(self):
        cleaned_data = super().clean()
        valid_from = cleaned_data.get('valid_from')
        valid_to = cleaned_data.get('valid_to')
        
        # التأكد من أن تاريخ الانتهاء بعد تاريخ البدء
        if valid_from and valid_to and valid_from >= valid_to:
            self.add_error('valid_to', 'تاريخ الانتهاء يجب أن يكون بعد تاريخ البدء')
        
        return cleaned_data 