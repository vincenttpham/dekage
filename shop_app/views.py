from django.core.paginator import Paginator
from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from shop_app.models import Category, Product, Image, Review, CartProduct, Cart, Order, Promo, Carousel, CarouselItem, ShippingMethod, Country, State, City
from user_app.models import User, Message
from django.db.models import Q
import datetime
from datetime import timedelta
import decimal
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.contrib.sessions.models import Session
import json
import re
import requests
import urllib.request
import xml.etree.ElementTree as ET
from django.core.mail import send_mail
from shop_app.paypal import PayPalClient
from paypalcheckoutsdk.orders import OrdersCreateRequest, OrdersCaptureRequest

# Create your views here.


def index(request):
    if 'purchase_value' in request.session:
        del request.session['purchase_value']
        request.session.clear()
        request.session.flush()
    request.session['carousel'] = "carousel"
    request.session['page'] = "home"
    carousel = ""
    if Carousel.objects.filter(default=True):
        carousel = Carousel.objects.get(default=True)
    carousel_items = CarouselItem.objects.filter(carousel=carousel).order_by('number')
    products = Product.objects.all().order_by('-created_at')
    category = Category.objects.all().order_by('number')
    expired_carts = Cart.objects.filter(user=None)
    month = datetime.datetime.today() - timedelta(days=30)
    old = month.timestamp()
    if expired_carts:
        for cart in expired_carts:
            cart_products = cart.products.all()
            if (datetime.datetime.now().timestamp() - cart.updated_at.timestamp()) >= 86400:
                for product_in_cart in cart_products:
                    product_in_cart.delete()
                cart.delete()
    if 'category' in request.session:
        if Category.objects.all():
            for cg in Category.objects.all():
                if request.session['category'] == cg.name:
                    products = Product.objects.filter(
                        category=Category.objects.get(name=cg.name)).order_by('-created_at')
                    if not products:
                        messages.error(request, "There are currently no items in this category.")
                    if 'search' in request.session:
                        products = Product.objects.filter(Q(name__icontains=request.session['search']) | Q(description__icontains=request.session['search']), category=Category.objects.get(name=cg.name)).order_by('-created_at')
                        if not products:
                            messages.error(request, '"' + request.session['search'] + '"' + " does not match any " + '"' + cg.name + '"' + " items.")
                    if 'sort_by' in request.session:
                        if request.session['sort_by'] == "oldest":
                            products = products.order_by('created_at')
                        elif request.session['sort_by'] == "most_popular":
                            products = products.order_by('-sales')
    elif 'search' in request.session:
        products = Product.objects.filter(Q(name__icontains=request.session['search']) | Q(description__icontains=request.session['search'])).order_by('-created_at')
        if not products:
            messages.error(
                request, '"' + request.session['search'] + '"' + " does not match any items.")
        if 'sort_by' in request.session:
            if request.session['sort_by'] == "oldest":
                products = products.order_by('created_at')
            elif request.session['sort_by'] == "most_popular":
                products = products.order_by('-sales')
    elif 'sort_by' in request.session:
        if request.session['sort_by'] == "oldest":
            products = Product.objects.all().order_by('created_at')
        elif request.session['sort_by'] == "most_popular":
            products = Product.objects.all().order_by('-sales')
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        unread_messages = Message.objects.filter(receiver=user, read=False)
        cart = Cart.objects.get(user=user)
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        context = {
            "carousel_items": carousel_items,
            "user": user,
            "products": products,
            "cart": cart,
            "page_object": page_object,
            "unread_messages": unread_messages,
            "category": category,
            "old": old,
        }
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        else:
            cart.delete()
            del request.session['cart_id']
        context = {
            "carousel_items": carousel_items,
            "products": products,
            "cart": cart,
            "page_object": page_object,
            "category": category,
            "old": old,
        }
    else:
        context = {
            "carousel_items": carousel_items,
            "products": products,
            "page_object": page_object,
            "category": category,
            "old": old,
        }
    return render(request, "index.html", context)


def product(request, id):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    product = Product.objects.get(id=id)
    images = Image.objects.filter(product=product).order_by('-default')
    related_products = Product.objects.filter(
        category__name=product.category.name).exclude(id=product.id).order_by('-sales')
    quantity = range(1, 11)
    ordered_products = Product.objects.all().order_by('-sales')
    best_sellers = [ordered_products[0], ordered_products[1], ordered_products[2]]
    month = datetime.datetime.today() - timedelta(days=30)
    old = month.timestamp()
    rating_total = 0
    rating_count = product.reviews.all().count()
    for review in product.reviews.all():
        rating_total += review.rating
    if rating_count == 0:
        average_rating = 0
    else:
        average_rating = round(rating_total / rating_count, 1)
    reviews = product.reviews.all().order_by('-created_at')
    if 'sort_reviews_by' in request.session:
        if request.session['sort_reviews_by'] == "rating":
            reviews = product.reviews.all().order_by('-rating')
    paginator = Paginator(reviews, 10)
    page_number = request.GET.get('page')
    page_object = paginator.get_page(page_number)
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        unread_messages = Message.objects.filter(receiver=user, read=False)
        cart = Cart.objects.get(user=user)
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        product_in_cart = cart.products.filter(product=product, cart=cart)
        available_quantity = 0
        if product_in_cart:
            product_in_cart = cart.products.get(product=product, cart=cart)
            available_quantity = (product.quantity - product_in_cart.quantity)
        context = {
            "user": user,
            "product": product,
            "cart": cart,
            "product_in_cart": product_in_cart,
            "unread_messages": unread_messages,
            "related_products": related_products,
            "quantity": quantity,
            "available_quantity": available_quantity,
            "old": old,
            "best_sellers": best_sellers,
            "images": images,
            "average_rating": average_rating,
            "reviews:": reviews,
            "page_object": page_object,
        }
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        product_in_cart = cart.products.filter(product=product, cart=cart)
        available_quantity = 0
        if product_in_cart:
            product_in_cart = cart.products.get(product=product, cart=cart)
            available_quantity = (product.quantity - product_in_cart.quantity)
        context = {
            "product": product,
            "cart": cart,
            "product_in_cart": product_in_cart,
            "related_products": related_products,
            "quantity": quantity,
            "available_quantity": available_quantity,
            "old": old,
            "best_sellers": best_sellers,
            "images": images,
            "average_rating": average_rating,
            "reviews:": reviews,
            "page_object": page_object,
        }
    else:
        context = {
            "product": product,
            "related_products": related_products,
            "quantity": quantity,
            "old": old,
            "best_sellers": best_sellers,
            "images": images,
            "average_rating": average_rating,
            "reviews:": reviews,
            "page_object": page_object,
        }
    return render(request, "product.html", context)


def cart(request):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'continue' in request.session:
        del request.session['continue']
    if 'first_name' in request.session:
        del request.session['first_name']
    if 'last_name' in request.session:
        del request.session['last_name']
    if 'email' in request.session:
        del request.session['email']
    if 'address' in request.session:
        del request.session['address']
    if 'address_2' in request.session:
        del request.session['address_2']
    if 'city' in request.session:
        del request.session['city']
    if 'country' in request.session:
        del request.session['country']
    if 'state' in request.session:
        del request.session['state']
    if 'zipcode' in request.session:
        del request.session['zipcode']
    if 'shipping_rate' in request.session:
        del request.session['shipping_rate']
    if 'shipping_method' in request.session:
        del request.session['shipping_method']
    quantity = range(1, 11)
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        unread_messages = Message.objects.filter(receiver=user, read=False)
        cart = Cart.objects.get(user=user)
        cart_products = cart.products.all()
        if not cart_products:
            cart.total = 0
            cart.quantity = 0
            #cart.promo_code = ""
            cart.promo_active = False
            cart.save()
        if cart.promo_active:
            promo = Promo.objects.get(code=cart.promo_code, active=True)
            discount = round(cart.total * promo.discount, 2)
            discount_total = round(cart.total - discount, 2)
            context = {
                "user": user,
                "cart": cart,
                "cart_products": cart_products,
                "promo": promo,
                "unread_messages": unread_messages,
                "quantity": quantity,
                "discount": discount,
                "discount_total": discount_total,
            }
        else:
            context = {
                "user": user,
                "cart": cart,
                "cart_products": cart_products,
                "unread_messages": unread_messages,
                "quantity": quantity,
            }
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        cart_products = cart.products.all()

        #    IF NOT UPDATING CART.QUANTITY DURING ADD/REMOVE FROM CART    #
        ##############
        # for product in cart_products:
        #   cart.quantity += product.quantity
        #   cart.save()

        if not cart_products:
            cart.total = 0
            cart.quantity = 0
            cart.promo_code = ""
            cart.promo_active = False
            cart.save()
        if cart.promo_active:
            promo = Promo.objects.get(code=cart.promo_code, active=True)
            discount = round(cart.total * promo.discount, 2)
            discount_total = round(cart.total - discount, 2)
            context = {
                "cart": cart,
                "cart_products": cart_products,
                "promo": promo,
                "quantity": quantity,
                "discount": discount,
                "discount_total": discount_total,
            }
        else:
            context = {
                "cart": cart,
                "cart_products": cart_products,
                "quantity": quantity,
            }
    else:
        context = {}
    return render(request, "cart.html", context)


def checkout(request):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    client_id = PayPalClient().client_id
    shipping_methods = ShippingMethod.objects.all().order_by('number')
    shipping_cost = round(decimal.Decimal(0.00), 2)
    if 'shipping_rate' in request.session:
        shipping_cost = decimal.Decimal(request.session['shipping_rate'])
    tax_rate = 0
    if City.objects.filter(default=True):
        city = City.objects.get(default=True)
        if 'country' in request.session and 'state' in request.session:
            if request.session['country'] == "US" and request.session['state'].upper() == "CA":
                tax_rate = city.tax_rate
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        unread_messages = Message.objects.filter(receiver=user, read=False)
        cart = Cart.objects.get(user=user)
        if 'shipping_method' in request.session:
            if cart.total >= 25 and request.session['shipping_method'] == "LETTER":
                shipping_cost = round(decimal.Decimal(0.00), 2)
        cart_products = cart.products.all()
        promo = ""
        discount = 0
        subtotal = cart.total
        tax = round(cart.total * tax_rate, 2)
        cart_total = round(cart.total + tax + shipping_cost, 2)
        if cart.promo_active:
            promo = Promo.objects.get(code=cart.promo_code, active=True)
            discount = round(cart.total * promo.discount, 2)
            subtotal = round(cart.total - discount, 2)
            tax = round(subtotal * tax_rate, 2)
            cart_total = round(subtotal + tax + shipping_cost, 2)
        context = {
            "user": user,
            "cart": cart,
            "client_id": client_id,
            "cart_products": cart_products,
            "unread_messages": unread_messages,
            "promo": promo,
            "discount": discount,
            "shipping_methods": shipping_methods,
            "shipping_cost": shipping_cost,
            "subtotal": subtotal,
            "tax": tax,
            "cart_total": cart_total,
        }
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        if 'shipping_method' in request.session:
            if cart.total >= 25 and request.session['shipping_method'] == "LETTER":
                shipping_cost = round(decimal.Decimal(0.00), 2)
        cart_products = cart.products.all()
        promo = ""
        discount = 0
        subtotal = cart.total
        tax = round(cart.total * tax_rate, 2)
        cart_total = round(cart.total + tax + shipping_cost, 2)
        if cart.promo_active:
            promo = Promo.objects.get(code=cart.promo_code, active=True)
            discount = round(cart.total * promo.discount, 2)
            subtotal = round(cart.total - discount, 2)
            tax = round(subtotal * tax_rate, 2)
            cart_total = round(subtotal + tax + shipping_cost, 2)
        context = {
            "cart": cart,
            "client_id": client_id,
            "cart_products": cart_products,
            "promo": promo,
            "discount": discount,
            "shipping_methods": shipping_methods,
            "shipping_cost": shipping_cost,
            "subtotal": subtotal,
            "tax": tax,
            "cart_total": cart_total,
        }
    else:
        return redirect('/cart')
    return render(request, "checkout.html", context)


def thank_you(request, order_id):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'continue' in request.session:
        del request.session['continue']
    if 'first_name' in request.session:
        del request.session['first_name']
    if 'last_name' in request.session:
        del request.session['last_name']
    if 'email' in request.session:
        del request.session['email']
    if 'address' in request.session:
        del request.session['address']
    if 'address_2' in request.session:
        del request.session['address_2']
    if 'city' in request.session:
        del request.session['city']
    if 'country' in request.session:
        del request.session['country']
    if 'state' in request.session:
        del request.session['state']
    if 'zipcode' in request.session:
        del request.session['zipcode']
    if 'shipping_rate' in request.session:
        del request.session['shipping_rate']
    if 'shipping_method' in request.session:
        del request.session['shipping_method']
    order = Order.objects.get(order_id=order_id)
    context = {
        "order_id": order.order_id,
    }
    return render(request, "thankyou.html", context)


def contact(request):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        cart = Cart.objects.get(user=user)
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        context = {
            "user": user,
            "cart": cart,
        }
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        context = {
            "cart": cart,
        }
    else:
        context = {}
    return render(request, "contact.html", context)


def terms(request):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        cart = Cart.objects.get(user=user)
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        context = {
            "user": user,
            "cart": cart,
        }
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        context = {
            "cart": cart,
        }
    else:
        context = {}
    return render(request, "terms.html", context)


def privacy(request):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        cart = Cart.objects.get(user=user)
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        context = {
            "user": user,
            "cart": cart,
        }
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        if cart.products.all():
            cart.quantity = 0
            for cart_product in cart.products.all():
                cart.quantity += cart_product.quantity
            cart.save()
        context = {
            "cart": cart,
        }
    else:
        context = {}
    return render(request, "privacy.html", context)


def filter(request, category):
    if Category.objects.all():
        for cg in Category.objects.all():
            if category == cg.name:
                request.session['category'] = cg.name
            elif category == 'all':
                if 'category' in request.session:
                    del request.session['category']
    return redirect('/')


def search(request):
    request.session['search'] = request.POST['search']
    return redirect('/')


def remove_search(request):
    del request.session['search']
    return redirect('/')


def sort(request):
    if request.POST['sort_by'] == "oldest":
        request.session['sort_by'] = "oldest"
    elif request.POST['sort_by'] == "most_popular":
        request.session['sort_by'] = "most_popular"
    elif request.POST['sort_by'] == "newest":
        if 'sort_by' in request.session:
            del request.session['sort_by']
    return redirect('/')


def submit_contact(request):
    if request.method == "POST":
        EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
        errors = {}
        if not EMAIL_REGEX.match(request.POST['email']):
            errors['email'] = "Please enter your email address in format: yourname@example.com"
        if len(errors) > 0:
            for key, value in errors.items():
                messages.warning(request, value, extra_tags=key)
                return redirect('/contact')
        try:
            send_mail(
                request.POST['email'] + ' - ' + request.POST['first_name'] + request.POST['last_name'],
                request.POST['message'],
                request.POST['email'],
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
        except BadHeaderError:
                return HttpResponse('Invalid header found.')
        messages.info(request, "Your message has been received. Please allow at least 2-3 days for a response from our team. Thank you.")
    else:
        messages.info(request, "Sorry, an internal error has occured. Please refresh the page and try again.")
        return redirect('/contact')
    return redirect('/')


def add_to_cart(request, id):
    if 'user_id' in request.session:
        user = User.objects.get(id=request.session["user_id"])
        if not Cart.objects.filter(user=user):
            cart = Cart.objects.create(user=user)
        else:
            cart = Cart.objects.get(user=user)
    elif 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
    else:
        session_cart = Cart.objects.create()
        request.session['cart_id'] = session_cart.id
        cart = Cart.objects.get(id=request.session['cart_id'])
    product = Product.objects.get(id=id)
    if not cart.products.filter(product=product):
        cart_product = CartProduct.objects.create(
            product=product)
        cart.products.add(cart_product)
    product_in_cart = CartProduct.objects.get(product=product, cart=cart)
    product_in_cart.quantity += int(request.POST['quantity'])
    cart.quantity += int(request.POST['quantity'])
    cart.save()
    price = product.price
    if product.discount_price:
        price = product.discount_price
    product_in_cart.total += (price * decimal.Decimal(request.POST['quantity']))
    product_in_cart.save()
    cart.total += (price * decimal.Decimal(request.POST['quantity']))
    cart.save()
    messages.info(request, '"' + product.name + '"' + " added to cart.")
    return redirect('/cart')


def remove_from_cart(request, id):
    if 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
    elif 'user_id' in request.session:
        user = User.objects.get(id=request.session["user_id"])
        cart = Cart.objects.get(user=user)
    product = Product.objects.get(id=id)
    product_in_cart = CartProduct.objects.get(product=product, cart=cart)
    cart.quantity -= product_in_cart.quantity
    cart.save()
    price = product.price
    if product.discount_price:
        price = product.discount_price
    cart.total -= (price * decimal.Decimal(product_in_cart.quantity))
    cart.save()
    product_in_cart.delete()
    messages.info(request, '"' + product.name + '"' + " removed from cart.")
    return redirect('/cart')


def change_quantity(request, id):
    if 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
    elif 'user_id' in request.session:
        user = User.objects.get(id=request.session["user_id"])
        cart = Cart.objects.get(user=user)
    product = Product.objects.get(id=id)
    cart_product = CartProduct.objects.get(product=product, cart=cart)
    if cart_product.quantity == int(request.POST.get('quantity')):
        messages.info(request, '"' + product.name + '"' + " x" + str(cart_product.quantity) + " already in cart. Item quantity not changed.")
        return redirect(f'/product/{id}')
    else:
        price = product.price
        if product.discount_price:
            price = product.discount_price
        if int(request.POST['quantity']) < cart_product.quantity:
            cart.quantity -= (cart_product.quantity - int(request.POST['quantity']))
            cart.total -= ((cart_product.quantity - int(request.POST['quantity'])) * price)
            cart_product.total -= ((cart_product.quantity - int(request.POST['quantity'])) * price)
        elif int(request.POST['quantity']) > cart_product.quantity:
            cart.quantity += (int(request.POST['quantity']) - cart_product.quantity)
            cart.total += ((int(request.POST['quantity']) - cart_product.quantity) * price)
            cart_product.total += ((int(request.POST['quantity']) - cart_product.quantity) * price)
        cart_product.quantity = request.POST['quantity']
        cart_product.save()
        cart.save()
        messages.info(request, '"' + product.name + '"' + " quantity changed to " + cart_product.quantity + ".")
    return redirect('/cart')


def promo(request):
    if 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        cart_products = cart.products.all()
        promo = Promo.objects.filter(code=request.POST["promo"], active=True)
        if cart.promo_active:
            messages.error(request, "Existing promo code already active.")
            return redirect('/cart')
        elif not promo:
            messages.error(request, "Promo code does not exist or is no longer active.")
            return redirect('/cart')
        elif not cart_products:
            messages.error(request, "Please add items to cart to redeem promo code.")
            return redirect('/cart')
        else:
            promo = Promo.objects.get(code=request.POST["promo"], active=True)
            discount_percent = int(promo.discount * 100)
            cart.promo_code = promo.code
            cart.promo_active = True
            cart.save()
            messages.info(request, "Promo code " + '"' + promo.code + '"' + " redeemed for " + str(discount_percent) + f"% off.")
    elif 'user_id' in request.session:
        user = User.objects.get(id=request.session["user_id"])
        cart = Cart.objects.get(user=user)
        cart_products = cart.products.all()
        promo = Promo.objects.filter(code=request.POST["promo"], active=True)
        if cart.promo_active:
            messages.error(request, "Existing promo code already active.")
            return redirect('/cart')
        elif not promo:
            messages.error(request, "Promo code does not exist or is inactive.")
            return redirect('/cart')
        elif not cart_products:
            messages.error(request, "Please add items to cart to redeem promo code.")
            return redirect('/cart')
        else:
            promo = Promo.objects.get(code=request.POST["promo"], active=True)
            discount_percent = int(promo.discount * 100)
            cart.promo_code = promo.code
            cart.promo_active = True
            cart.save()
            messages.info(request, "Promo code " + '"' + promo.code + '"' + " redeemed for " + str(discount_percent) + f"% off.")
    else:
        messages.error(request, "Please add items to cart to redeem promo code.")
    return redirect('/cart')


def remove_promo(request):
    if 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        promo = Promo.objects.get(code=cart.promo_code, active=True)
        cart.promo_code = ""
        cart.promo_active = False
        cart.save()
        messages.info(request, "Promo code " + '"' + promo.code + '"' + " removed.")
    elif 'user_id' in request.session:
        user = User.objects.get(id=request.session['user_id'])
        cart = Cart.objects.get(user=user)
        promo = Promo.objects.get(code=cart.promo_code, active=True)
        cart.promo_code = ""
        cart.promo_active = False
        cart.save()
        messages.info(request, "Promo code " + '"' + promo.code + '"' + " removed.")
    return redirect('/cart')


def continue_checkout(request, id):
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')
    errors = {}
    if not EMAIL_REGEX.match(request.POST['email']):
        errors['email'] = "Please enter your email address in format: yourname@example.com"
    if len(errors) > 0:
        for key, value in errors.items():
            messages.warning(request, value, extra_tags=key)
    else:
        request.session['continue'] = "continue"
        request.session['email'] = request.POST['email']
        usps_user_id = settings.USPS_USER_ID
        cart = Cart.objects.get(id=id)
        ounces = decimal.Decimal(0.35274)
        for cart_product in cart.products.all():
            ounces += (cart_product.quantity * cart_product.product.weight)
        service = "FIRST CLASS"
        mail_type = request.POST['shipping_method']
        machinable = "false"
        if request.POST['shipping_method'] == "LETTER" and ounces <= 1:
            machinable = "true"
        zip_destination = request.POST['zipcode']
        requestXML = f"""
        <?xml version="1.0"?>
        <RateV4Request USERID="{usps_user_id}">
            <Package ID="1ST">
                <Service>{service}</Service>
                <FirstClassMailType>{mail_type}</FirstClassMailType>
                <ZipOrigination>92612</ZipOrigination>
                <ZipDestination>{zip_destination}</ZipDestination>
                <Pounds>0</Pounds>
                <Ounces>{ounces}</Ounces>
                <Container></Container>
                <Machinable>{machinable}</Machinable>
            </Package>
        </RateV4Request>
        """
        docString = requestXML
        docString = docString.replace('\n','').replace('\t','')
        docString = urllib.parse.quote_plus(docString)
        url = "https://secure.shippingapis.com/ShippingAPI.dll?API=RateV4&XML=" + docString
        response = urllib.request.urlopen(url)
        if response.getcode() != 200:
            print("Error making HTTP call:")
            print(response.info())
            return redirect('/checkout')
        contents = response.read()
        root = ET.fromstring(contents)
        for package in root.findall('Package'):
            for postage in package.findall('Postage'):
                request.session['shipping_rate'] = postage.find("Rate").text
                request.session['shipping_method'] = request.POST['shipping_method']
    request.session['first_name'] = request.POST['first_name']
    request.session['last_name'] = request.POST['last_name']
    request.session['address'] = request.POST['address']
    request.session['address_2'] = request.POST['address_2']
    request.session['city'] = request.POST['city']
    request.session['country'] = request.POST['country']
    request.session['state'] = request.POST['state']
    request.session['zipcode'] = request.POST['zipcode']
    return redirect('/checkout')


def return_checkout(request):
    if 'continue' in request.session:
        del request.session['continue']
    return redirect('/checkout')


def review(request, id):
    if 'review' in request.session:
        del request.session['review']
    if 'update_review' in request.session:
        del request.session['update_review']
    if 'existing_review' in request.session:
        del request.session['exisiting_review']
    if 'order_id' in request.session:
        del request.session['order_id']
    if 'email' in request.session:
        del request.session['email']
    product = Product.objects.get(id=id)
    reviews = Review.objects.all()
    orders = Order.objects.filter(order_id=request.POST['order_id'])
    if orders:
        order = Order.objects.get(order_id=request.POST['order_id'])
        ordered_product = order.products.filter(product=product)
        if len(reviews.filter(email=order.email, product=product)) > 0:
            request.session['existing_review'] = product.id
            request.session['update_review'] = product.id
            request.session['order_id'] = request.POST['order_id']
            request.session['email'] = order.email
            messages.error(request, "A review from " + order.email + " already exists.")
        elif ordered_product:
            request.session['review'] = product.id
            request.session['order_id'] = request.POST['order_id']
            messages.info(request, "Order with matching ID has been found.")
        else:
            messages.error(request, "The order ID entered does not contain this product.")
    else:
        messages.error(request, "The order ID entered does not exist.")
    return redirect(f'/product/{id}')


def submit_review(request, id):
    product = Product.objects.get(id=id)
    reviews = Review.objects.all()
    errors = {}
    if 'rating' not in request.POST:
        errors['rating'] = "Please select a star rating."
    if len(request.POST['username']) < 3:
        errors['username'] = "Name must be a minimum of 3 characters."
    if len(request.POST['review_body']) < 3:
        errors['review_body'] = "Review body must be a minimum of 3 characters."
    if len(errors) > 0:
        for key, value in errors.items():
            messages.warning(request, value, extra_tags=key)
        return redirect(f'/product/{id}')
    else:
        order = Order.objects.get(order_id=request.session['order_id'])
        if 'update_review' in request.session:
            review = Review.objects.get(email=order.email, product=product)
            review.username = request.POST['username']
            review.rating = request.POST['rating']
            review.body = request.POST['review_body']
            review.updated = True
            review.save()
            messages.info(request, "Review has been updated.")
        else:
            if len(reviews.filter(username=request.POST['username'], product=product)) > 0:
                messages.info(request, "A review with this name already exists.")
                return redirect(f'/product/{id}')
            review = Review.objects.create(order_id=request.session['order_id'], username=request.POST['username'], email=order.email, rating=request.POST['rating'], body=request.POST['review_body'], product=product)
            messages.info(request, "Review has been submitted.")
    if 'review' in request.session:
        del request.session['review']
    if 'update_review' in request.session:
        del request.session['update_review']
    if 'existing_review' in request.session:
        del request.session['existing_review']
    if 'order_id' in request.session:
        del request.session['order_id']
    if 'email' in request.session:
        del request.session['email']
    return redirect(f'/product/{id}')


def update_review(request, id):
    product = Product.objects.get(id=id)
    request.session['review'] = product.id
    del request.session['existing_review']
    return redirect(f'/product/{id}')


def cancel_update_review(request, id):
    if 'review' in request.session:
        del request.session['review']
    if 'update_review' in request.session:
        del request.session['update_review']
    if 'existing_review' in request.session:
        del request.session['existing_review']
    if 'order_id' in request.session:
        del request.session['order_id']
    if 'email' in request.session:
        del request.session['email']
    return redirect(f'/product/{id}')


def sort_reviews(request, id):
    if request.POST['sort_reviews_by'] == "rating":
        request.session['sort_reviews_by'] = "rating"
    elif request.POST['sort_reviews_by'] == "newest":
        if 'sort_reviews_by' in request.session:
            del request.session['sort_reviews_by']
    return redirect(f'/product/{id}')


def create_order(request, id):
    if request.method == "POST":
        cart = Cart.objects.get(id=id)
        create = OrdersCreateRequest()
        shipping_cost = 0
        shipping_discount = 0
        if 'shipping_rate' in request.session:
            shipping_cost = decimal.Decimal(request.session['shipping_rate'])
        if cart.total >= 25 and request.session['shipping_method'] == "LETTER":
            shipping_discount = decimal.Decimal(request.session['shipping_rate'])
        tax_rate = 0
        if City.objects.filter(default=True):
            city = City.objects.get(default=True)
            if request.session['state'] == city.state.abbreviation:
                tax_rate = city.tax_rate
        discount = 0
        tax = round(cart.total * tax_rate, 2)
        total = round(cart.total + tax + shipping_cost - shipping_discount, 2)
        if cart.promo_active:
            promo = Promo.objects.get(code=cart.promo_code, active=True)
            discount = round(cart.total * promo.discount, 2)
            subtotal = round(cart.total - discount, 2)
            tax = round(subtotal * tax_rate, 2)
            total = round(subtotal + tax + shipping_cost - shipping_discount, 2)
        request.session['purchase_value'] = float(total)
        items = []
        for cart_product in cart.products.all():
            price = cart_product.product.price
            if cart_product.product.discount_price:
                price = cart_product.product.discount_price
            item = {
                "name": cart_product.product.name,
                "unit_amount": {
                    "currency_code": "USD",
                    "value": float(price)
                },
                "tax": {
                    "currency_code": "USD",
                    "value": "0.00"
                },
                "quantity": cart_product.quantity,
                "category": "PHYSICAL_GOODS"
            }
            items.append(item)
        create.request_body (
            {
                "intent": "CAPTURE",
                "application_context": {
                    "brand_name": "Dekage",
                    "landing_page": "BILLING",
                    "shipping_preference": "SET_PROVIDED_ADDRESS",
                    "user_action": "CONTINUE"
                },
                "payer": {
                    "email_address": request.session['email'],
                },
                "purchase_units": [
                    {
                        "amount": {
                            "currency_code": "USD",
                            "value": float(total),
                            "breakdown": {
                                "item_total": {
                                    "currency_code": "USD",
                                    "value": float(cart.total),
                                },
                                "shipping": {
                                    "currency_code": "USD",
                                    "value": float(shipping_cost)
                                },
                                "handling": {
                                    "currency_code": "USD",
                                    "value": "0.00"
                                },
                                "tax_total": {
                                    "currency_code": "USD",
                                    "value": float(tax)
                                },
                                "shipping_discount": {
                                    "currency_code": "USD",
                                    "value": float(shipping_discount)
                                },
                                "discount": {
                                    "currency_code": "USD",
                                    "value": float(discount)
                                }
                            }
                        },
                        "items": items,
                        "shipping": {
                            "method": "United States Postal Service",
                            "address": {
                                "name": {
                                    "full_name": request.session['first_name'],
                                    "surname": request.session['last_name']
                                },
                                "address_line_1": request.session['address'],
                                "address_line_2": request.session['address_2'],
                                "admin_area_2": request.session['city'],
                                "admin_area_1": request.session['state'],
                                "postal_code": request.session['zipcode'],
                                "country_code": request.session['country']
                            }
                        }
                    }
                ]
            }
        )
        response = PayPalClient().client.execute(create)
        data = response.result.__dict__['_dict']
        return JsonResponse(data)
    else:
        return JsonResponse({'details': "invalid request"})


def capture_order(request, order_id, id):
    if request.method == "POST":
        if 'cart_id' in request.session:
            cart = Cart.objects.get(id=request.session['cart_id'])
            cart.order_id = order_id
            cart.save()
        capture = OrdersCaptureRequest(order_id)
        response = PayPalClient().client.execute(capture)
        data = response.result.__dict__['_dict']
        return JsonResponse(data)
    else:
        return JsonResponse({'details': "invalid request"})


def order_placed(request):
    order_id = ""
    if 'cart_id' in request.session:
        cart = Cart.objects.get(id=request.session['cart_id'])
        new_order = Order.objects.create(order_id=cart.order_id)
        order = Order.objects.get(order_id=cart.order_id)
        order.email = request.session['email']
        order_id = cart.order_id
        if cart.products.all():
            for cart_product in cart.products.all():
                db_product = Product.objects.get(id=cart_product.product.id)
                db_product.quantity -= int(cart_product.quantity)
                db_product.sales += int(cart_product.quantity)
                db_product.save()
                cart.products.remove(cart_product)
                cart.save()
                order.products.add(cart_product)
                order.save()
        send_mail(
                'Order: ' + order.order_id,
                'Thank you for shopping at dekageshop.com. If you like your items, consider leaving us a review using the order ID.',
                settings.EMAIL_HOST_USER,
                [order.email],
                fail_silently=False,
            )
    elif 'user_id' in request.session:
        user = User.objects.get(id=request.session["user_id"])
        cart = Cart.objects.get(user=user)
        new_order = Order.objects.create(order_id=cart.order_id)
        order = Order.objects.get(order_id=cart.order_id)
        order.email = request.session['email']
        order_id = cart.order_id
        if cart.products.all():
            for cart_product in cart.products.all():
                db_product = Product.objects.get(id=cart_product.product.id)
                db_product.quantity -= int(cart_product.quantity)
                db_product.sales += int(cart_product.quantity)
                db_product.save()
                cart.products.remove(cart_product)
                cart.save()
                order.products.add(cart_product)
                order.save()
        send_mail(
                'Order: ' + order.order_id,
                'Thank you for shopping at dekageshop.com. If you like your items, consider leaving us a review using the order ID.',
                settings.EMAIL_HOST_USER,
                [order.email],
                fail_silently=False,
            )
    if 'email' in request.session:
        del request.session['email']
    return redirect('/thankyou/' + order_id)