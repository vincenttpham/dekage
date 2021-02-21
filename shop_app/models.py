from __future__ import unicode_literals
from django.db import models
from user_app.models import User
import datetime

# Create your models here.


class Category(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    discount_price = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    quantity = models.IntegerField(default=0)
    sales = models.IntegerField(default=0)
    weight = models.DecimalField(max_digits=15, decimal_places=6, default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return self.name


class Image(models.Model):
    img = models.ImageField(upload_to="products/")
    default = models.BooleanField(default=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")

    def __str__(self):
        return self.product.name + " " + str(self.id)


class Review(models.Model):
    order_id = models.CharField(max_length=255)
    username = models.CharField(max_length=255)
    email = models.EmailField(max_length=255, blank=True)
    rating = models.IntegerField(default=0)
    body = models.TextField(blank=True)
    updated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")

    def __str__(self):
        return self.username + " - " + self.product.name


class CartProduct(models.Model):
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return "(" + str(self.quantity) + ")" + self.product.name


class Cart(models.Model):
    total = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    quantity = models.IntegerField(default=0)
    promo_code = models.CharField(max_length=255, blank=True)
    promo_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    products = models.ManyToManyField(CartProduct, related_name="cart")
    order_id = models.CharField(max_length=255, blank=True)

    def __str__(self):
        if self.user:
            return self.user.first_name + " " + self.user.last_name
        return str(self.created_at)


class Order(models.Model):
    order_id = models.CharField(max_length=255)
    email = models.EmailField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    products = models.ManyToManyField(CartProduct, related_name="order")

    def __str__(self):
        return self.order_id + " - " + str(self.id)


class Promo(models.Model):
    code = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code


class Carousel(models.Model):
    name = models.CharField(max_length=255)
    default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class CarouselItem(models.Model):
    header = models.CharField(max_length=255, blank=True)
    subheader = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    number = models.IntegerField(default=0)
    img = models.ImageField(upload_to="carousel/")
    carousel = models.ForeignKey(Carousel, on_delete=models.CASCADE, related_name="items")

    def __str__(self):
        return self.carousel.name + " " + str(self.id)


class ShippingMethod(models.Model):
    number = models.IntegerField(default=0)
    name = models.CharField(max_length=255)
    service = models.CharField(max_length=255)
    mail_type = models.CharField(max_length=255)
    default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Country(models.Model):
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class State(models.Model):
    name = models.CharField(max_length=255)
    abbreviation = models.CharField(max_length=255)
    tax_rate = models.DecimalField(max_digits=15, decimal_places=5, default=0.0)
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name="states")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class City(models.Model):
    name = models.CharField(max_length=255)
    tax_rate = models.DecimalField(max_digits=15, decimal_places=5, default=0.0)
    default = models.BooleanField(default=False)
    state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="cities")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name