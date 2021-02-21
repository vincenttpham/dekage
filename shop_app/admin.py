from django.contrib import admin
from shop_app.models import Category, Product, Image, Review, CartProduct, Cart, Order, Promo, Carousel, CarouselItem, ShippingMethod, Country, State, City
from django.db import models

# Register your models here.

class ImageInline(admin.TabularInline):
    model = Image

class ProductAdmin(admin.ModelAdmin):
    inlines = [
        ImageInline,
    ]

class CarouselItemInline(admin.StackedInline):
    model = CarouselItem

class CarouselAdmin(admin.ModelAdmin):
    inlines = [
        CarouselItemInline,
    ]

admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Image)
admin.site.register(Review)
admin.site.register(CartProduct)
admin.site.register(Cart)
admin.site.register(Order)
admin.site.register(Promo)
admin.site.register(Carousel, CarouselAdmin)
admin.site.register(CarouselItem)
admin.site.register(ShippingMethod)
admin.site.register(Country)
admin.site.register(State)
admin.site.register(City)