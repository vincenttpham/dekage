from django.shortcuts import render, HttpResponse, redirect
from django.contrib import messages
from user_app.models import User, UserManager, Message
from shop_app.models import Category, Product, Review, CartProduct, Cart, Order, Promo
from django.db.models import Q
import bcrypt
import datetime
from datetime import timedelta
import random

# Create your views here.


def login(request):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' in request.session:
        return redirect('/user')
    return render(request, "login.html")


def log(request):
    user = User.objects.filter(email=request.POST["email"])
    if not user:
        messages.error(request, "Email address not found.")
        return redirect("/user/login")
    logged_user = user[0]
    if bcrypt.checkpw(request.POST['password'].encode(), logged_user.password.encode()):
        request.session["user_id"] = logged_user.id
        if 'cart_id' in request.session:
            del request.session['cart_id']
        return redirect("/")
    else:
        messages.error(request, "Invalid email/password combination.")
        return redirect("/user/login")


def logout(request):
    request.session.flush()
    request.session.clear()
    return redirect("/")


def register(request):
    if 'page' in request.session:
        del request.session['page']
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' in request.session:
        return redirect('/user')
    return render(request, "register.html")


def reg(request):
    errors = User.objects.registration_validator(request.POST)
    if len(errors) > 0:
        for key, value in errors.items():
            messages.error(request, value, extra_tags=key)
        return redirect("/user/register")
    else:
        password = request.POST["password"]
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = User.objects.create(
            first_name=request.POST["first_name"], last_name=request.POST["last_name"], username=request.POST["username"], email=request.POST["email"], password=pw_hash)
        cart = Cart.objects.create(user=user)
        admin_account = User.objects.filter(
            first_name="Admin", last_name="Buttery", username="butteryadmin", email="admin@butterygrind.com")
        if admin_account:
            admin_account = User.objects.get(
                first_name="Admin", last_name="Buttery", username="butteryadmin", email="admin@butterygrind.com")
            msg = Message.objects.create(
                body='Thank you for registering with The Buttery Grind. As a thank-you gift for shopping with us, enter code "BUTTERY" at checkout to redeem $20 off your first order.', sender=admin_account)
            msg.receiver.add(user)
            msg.save()
        request.session["user_id"] = user.id
        return redirect("/")


def orders(request):
    request.session['page'] = "account"
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' not in request.session:
        return redirect('/user/login')
    user = User.objects.get(id=request.session['user_id'])
    cart = Cart.objects.get(user=user)
    cart_products = cart.products.all()
    if not cart_products:
        cart.total = 0
        cart.quantity = 0
        cart.promo_code = ""
        cart.promo_active = False
        cart.save()
    if 'sort_by' in request.session:
        orders = Order.objects.filter(
            user=user, shipped=False).order_by('created_at')
    else:
        orders = Order.objects.filter(
            user=user, shipped=False).order_by('-created_at')
    eta = random.randrange(2, 5)
    unread_messages = user.message.filter(read=False)
    context = {
        "user": user,
        "cart": Cart.objects.get(user=user),
        "orders": orders,
        "eta": eta,
        "unread_messages": unread_messages,
    }
    return render(request, "orders.html", context)


def sort_by(request):
    if request.POST['sort_by'] == 'oldest':
        request.session['sort_by'] = 'oldest'
    elif request.POST['sort_by'] == 'newest':
        if 'sort_by' in request.session:
            del request.session['sort_by']
    return redirect('/user')


def history(request):
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' not in request.session:
        return redirect('/user/login')
    user = User.objects.get(id=request.session['user_id'])
    orders = Order.objects.filter(user=user, shipped=False)
    shipped_orders = Order.objects.filter(user=user, shipped=True)
    today = datetime.datetime.today()
    yesterday = today - timedelta(days=1)
    two_days = today - timedelta(days=2)
    orders_today = Order.objects.filter(
        user=user, shipped=True, updated_at__gt=yesterday)
    orders_yesterday = Order.objects.filter(
        user=user, shipped=True, updated_at__lt=yesterday, updated_at__gt=two_days)
    old_orders = Order.objects.filter(
        user=user, shipped=True, updated_at__lt=two_days)
    unread_messages = user.message.filter(read=False)
    context = {
        "user": user,
        "cart": Cart.objects.get(user=user),
        "orders": orders,
        "shipped_orders": shipped_orders,
        "orders_today": orders_today,
        "orders_yesterday": orders_yesterday,
        "old_orders": old_orders,
        "unread_messages": unread_messages,
    }
    return render(request, "history.html", context)


def message_view(request):
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' not in request.session:
        return redirect('/user/login')
    user = User.objects.get(id=request.session['user_id'])
    unread_messages = user.message.filter(read=False)
    orders = Order.objects.filter(user=user, shipped=False)
    users_unread = set()
    users_other = set()
    if 'user_search' in request.session:
        user_list = User.objects.filter(
            Q(first_name__icontains=request.session['user_search']) | Q(last_name__icontains=request.session['user_search']) | Q(username__icontains=request.session['user_search'])).exclude(id=user.id)
        if not user_list:
            messages.error(
                request, '"' + request.session['user_search'] + '"' + " does not match any users.")
    else:
        unread_person = ()
        user_list = User.objects.filter().exclude(id=user.id).order_by('last_name')
        for person in user_list:
            for msg in unread_messages:
                if msg.sender == person:
                    users_unread.add(person)
                    unread_person = person
            if person != unread_person:
                users_other.add(person)
    if 'other_user' in request.session:
        other_user = User.objects.get(id=request.session['other_user'])
        user_messages = Message.objects.filter(
            sender__id=request.session['other_user'], receiver=user)
        chat_messages = Message.objects.filter(
            Q(sender__id=request.session['other_user'], receiver=user) | Q(sender=user, receiver__id=request.session['other_user'])).order_by('created_at')
        today = datetime.date.today()
        context = {
            "user": user,
            "other_user": other_user,
            "user_list": user_list,
            "users_unread": users_unread,
            "users_other": users_other,
            "cart": Cart.objects.get(user=user),
            "orders": orders,
            "user_messages": user_messages,
            "unread_messages": unread_messages,
            "chat_messages": chat_messages,
            "today": today,
        }
    else:
        context = {
            "user": user,
            "user_list": user_list,
            "users_unread": users_unread,
            "users_other": users_other,
            "cart": Cart.objects.get(user=user),
            "orders": orders,
            "unread_messages": unread_messages,
        }
    return render(request, "messages.html", context)


def read_message(request, id):
    user = User.objects.get(id=request.session['user_id'])
    other_user = User.objects.get(id=id)
    request.session['other_user'] = other_user.id
    chat_messages = Message.objects.filter(sender=other_user, receiver=user)
    for msg in chat_messages:
        msg.read = True
        msg.save()
    return redirect("/user/messages")


def close_message(request):
    if 'other_user' in request.session:
        del request.session['other_user']
    return redirect("/user/messages")


def send_message(request):
    user = User.objects.get(id=request.session['user_id'])
    other_user = User.objects.get(id=request.session['other_user'])
    msg = Message.objects.create(body=request.POST['body'], sender=user)
    msg.receiver.add(other_user)
    chat_messages = Message.objects.filter(sender=other_user, receiver=user)
    for msg in chat_messages:
        msg.read = True
        msg.save()
    return redirect("/user/messages")


def user_search(request):
    request.session['user_search'] = request.POST['user_search']
    return redirect('/user/messages')


def user_remove_search(request):
    del request.session['user_search']
    return redirect('/user/messages')


def account(request):
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' not in request.session:
        return redirect('/user/login')
    user = User.objects.get(id=request.session['user_id'])
    orders = Order.objects.filter(user=user, shipped=False)
    unread_messages = user.message.filter(read=False)
    context = {
        "user": user,
        "cart": Cart.objects.get(user=user),
        "orders": orders,
        "unread_messages": unread_messages,
    }
    return render(request, "account.html", context)


def billing(request):
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' not in request.session:
        return redirect('/user/login')
    user = User.objects.get(id=request.session['user_id'])
    orders = Order.objects.filter(user=user, shipped=False)
    unread_messages = user.message.filter(read=False)
    context = {
        "user": user,
        "cart": Cart.objects.get(user=user),
        "orders": orders,
        "unread_messages": unread_messages,
    }
    return render(request, "billing.html", context)


def notifications(request):
    if 'carousel' in request.session:
        del request.session['carousel']
    if 'user_id' not in request.session:
        return redirect('/user/login')
    user = User.objects.get(id=request.session['user_id'])
    orders = Order.objects.filter(user=user, shipped=False)
    unread_messages = user.message.filter(read=False)
    context = {
        "user": user,
        "cart": Cart.objects.get(user=user),
        "orders": orders,
        "unread_messages": unread_messages,
    }
    return render(request, "notifications.html", context)


def update_account(request):
    user = User.objects.filter(id=request.session['user_id'])
    logged_user = user[0]
    errors = User.objects.update_validator(request.POST)
    if len(errors) > 0:
        for key, value in errors.items():
            messages.error(request, value, extra_tags=key)
        return redirect("/user/settings/account/")
    if bcrypt.checkpw(request.POST['current_password'].encode(), logged_user.password.encode()):
        user = User.objects.get(id=request.session['user_id'])
        password = request.POST["password"]
        pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user.first_name = request.POST["first_name"]
        user.last_name = request.POST["last_name"]
        user.username = request.POST["username"]
        user.email = request.POST["email"]
        user.password = pw_hash
        user.save()
        messages.info(request, "Successfully updated account info.")
        return redirect("/user/settings/account")
    else:
        messages.error(request, "Current password is incorrect.")
        return redirect("/user/settings/account")


def update_billing(request):
    user = User.objects.get(id=request.session['user_id'])
    user.country = request.POST["country"]
    user.address1 = request.POST["address1"]
    user.address2 = request.POST["address2"]
    user.city = request.POST["city"]
    user.state = request.POST["state"]
    user.zipcode = request.POST["zipcode"]
    user.save()
    messages.info(request, "Successfully updated billing info.")
    return redirect("/user/settings/billing")


def cancel_order(request, id):
    order = Order.objects.get(id=id)
    for product in order.products.all():
        product.delete()
    order.delete()
    return redirect('/user')
