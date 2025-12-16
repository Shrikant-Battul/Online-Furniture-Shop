from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegistrationForm, LoginForm, CheckoutForm
from .models import Category, Product, Order, OrderItem


def _placeholder_products(category_slug: str):
    seeds = {
        "chairs": [("Ergo Comfort Chair", 4999, "chair1"), ("Solid Wood Chair", 3499, "chair2")],
        "tables": [("Oak Dining Table", 9999, "table1"), ("Glass Coffee Table", 5999, "table2")],
        "beds": [("Queen Size Bed", 14999, "bed1"), ("Storage Bed", 17499, "bed2")],
        "sofas": [("2-Seater Fabric Sofa", 12999, "sofa1"), ("L-Shaped Sectional", 24999, "sofa2")],
        "wardrobes": [("2-Door Wardrobe", 10499, "wardrobe1"), ("3-Door Wardrobe", 13999, "wardrobe2")],
        "office": [("Ergo Office Chair", 6499, "office1"), ("Standing Desk", 11999, "office2")],
        "outdoor": [("Patio Set (4 pcs)", 8999, "outdoor1"), ("Garden Chair", 1999, "outdoor2")],
        "kids": [("Kids Bunk Bed", 13499, "kids1"), ("Study Table", 3299, "kids2")],
    }
    items = []
    for name, price, seed in seeds.get(category_slug, [])[:2]:
        items.append({
            "name": name,
            "price": price,
            "image_url": f"https://picsum.photos/seed/{seed}/600/450",
        })
    return items


def _category_page(request, slug: str, title: str):
    products_qs = Product.objects.filter(category__slug=slug)
    products = []
    for p in products_qs:
        products.append({
            "id": p.id,
            "name": p.name,
            "price": p.price,
            "image_url": p.image.url if p.image else None,
        })
    if not products:
        products = _placeholder_products(slug)
    return render(request, 'category.html', {"title": title, "products": products})


def home(request):
    return render(request, 'home.html')


def about(request):
    return render(request, 'about.html')


def contact(request):
    return render(request, 'contact.html')


def furniture_menu(request):
    cats = [
        ("Chairs", "chairs"),
        ("Tables", "tables"),
        ("Beds", "beds"),
        ("Sofas", "sofas"),
        ("Wardrobes", "wardrobes"),
        ("Office", "office"),
        ("Outdoor", "outdoor"),
        ("Kids", "kids"),
    ]
    # If categories exist in DB, prefer them
    db_cats = Category.objects.all()
    if db_cats.exists():
        cats = [(c.name, c.slug) for c in db_cats]
    return render(request, 'furniture_menu.html', {"categories": cats})


def chairs(request):
    return _category_page(request, 'chairs', 'Chairs')


def tables(request):
    return _category_page(request, 'tables', 'Tables')


def beds(request):
    return _category_page(request, 'beds', 'Beds')


def sofas(request):
    return _category_page(request, 'sofas', 'Sofas')


def wardrobes(request):
    return _category_page(request, 'wardrobes', 'Wardrobes')


def office_furniture(request):
    return _category_page(request, 'office', 'Office Furniture')


def outdoor_furniture(request):
    return _category_page(request, 'outdoor', 'Outdoor Furniture')


def kids_furniture(request):
    return _category_page(request, 'kids', "Kids' Furniture")


def category_dynamic(request, slug: str):
    # Try to get a category by slug; if not found, still render using placeholder seed
    title = slug.replace('-', ' ').title()
    try:
        cat = Category.objects.get(slug=slug)
        title = cat.name
    except Category.DoesNotExist:
        pass
    return _category_page(request, slug, title)


def cart(request):
    cart = request.session.get('cart', {})
    product_ids = [int(pid) for pid in cart.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    items = []
    total = 0
    for pid_str, entry in cart.items():
        pid = int(pid_str)
        qty = entry.get('qty', 1)
        p = products.get(pid)
        if not p:
            continue
        line_total = float(p.price) * qty
        total += line_total
        items.append({
            'id': pid,
            'name': p.name,
            'price': p.price,
            'qty': qty,
            'image_url': p.image.url if p.image else None,
            'line_total': line_total,
        })
    return render(request, 'cart.html', {'items': items, 'total': total})


def checkout(request):
    # Build cart items from session for summary and order creation
    cart = request.session.get('cart', {})
    product_ids = [int(pid) for pid in cart.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=product_ids)}
    items = []
    total = 0
    for pid_str, entry in cart.items():
        pid = int(pid_str)
        qty = entry.get('qty', 1)
        p = products.get(pid)
        if not p:
            continue
        line_total = float(p.price) * qty
        total += line_total
        items.append({'product': p, 'qty': qty, 'line_total': line_total})

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if not items:
            messages.error(request, 'Your cart is empty.')
            return redirect('cart')
        if form.is_valid():
            order = Order.objects.create(
                name=form.cleaned_data['name'],
                phone=form.cleaned_data['phone'],
                email=form.cleaned_data['email'],
                address=form.cleaned_data['address'],
                city=form.cleaned_data['city'],
                postal_code=form.cleaned_data['postal_code'],
                payment_method=form.cleaned_data['payment_method'],
                total=total,
            )
            # Create order items
            for it in items:
                OrderItem.objects.create(
                    order=order,
                    product=it['product'],
                    price=it['product'].price,
                    qty=it['qty'],
                )
            # Clear cart
            request.session['cart'] = {}
            request.session.modified = True
            # For both UPI and COD, show a Pending page until admin processes the order
            messages.info(request, 'Order placed and currently pending. You will be notified after processing.')
            return redirect('order_pending', order_id=order.id)
    else:
        form = CheckoutForm()

    return render(request, 'checkout.html', {'form': form, 'items': items, 'total': total})


def payment_methods(request):
    return render(request, 'payment_methods.html')


def order_pay(request, order_id: int):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('/')
    if request.method == 'POST':
        # user confirms they have paid, optionally provide reference
        ref = request.POST.get('payment_reference', '').strip()
        if ref:
            order.payment_reference = ref
        order.status = Order.STATUS_AWAITING
        order.save()
        messages.success(request, 'Thanks! We\'ll verify your payment shortly.')
        return redirect('payment_methods')
    return render(request, 'order_pay.html', {'order': order})


def order_pending(request, order_id: int):
    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        messages.error(request, 'Order not found.')
        return redirect('/')
    return render(request, 'order_pending.html', {'order': order})


def order_status(request, order_id: int):
    try:
        order = Order.objects.only('status').get(id=order_id)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'not_found'}, status=404)
    return JsonResponse({'status': order.status})


# --- Simple session cart ---
def _get_cart(session):
    return session.get('cart', {})


def _save_cart(session, cart):
    session['cart'] = cart
    session.modified = True


def cart_add(request, product_id: int):
    cart = _get_cart(request.session)
    key = str(int(product_id))
    entry = cart.get(key, {'qty': 0})
    entry['qty'] = entry.get('qty', 0) + 1
    cart[key] = entry
    _save_cart(request.session, cart)
    messages.success(request, 'Added to cart.')
    return redirect('cart')


def cart_remove(request, product_id: int):
    cart = _get_cart(request.session)
    key = str(int(product_id))
    if key in cart:
        del cart[key]
        _save_cart(request.session, cart)
        messages.info(request, 'Removed from cart.')
    return redirect('cart')


# Auth views
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created. You can now log in.')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Handle explicit Resend OTP action
            if request.POST.get('resend_otp'):
                session_username = request.session.get('login_username')
                if not session_username:
                    messages.info(request, 'Please enter your username and password first to generate an OTP.')
                    return render(request, 'login.html', {'form': form})
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(username=session_username)
                except User.DoesNotExist:
                    messages.error(request, 'Session expired. Please login again.')
                    return redirect('login')
                # Regenerate and send OTP
                import random
                otp_code = f"{random.randint(1000, 9999)}"
                request.session['login_otp'] = otp_code
                request.session.modified = True
                recipient = getattr(user, 'email', '') or ''
                if recipient:
                    try:
                        send_mail(
                            subject='Your Login OTP',
                            message=f'Hello, thanks for selecting our shop.\nHere is your OTP: {otp_code}\nThank you — HAPPY SHOPPINGGGG',
                            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                            recipient_list=[recipient],
                            fail_silently=False,
                        )
                        messages.success(request, 'A new OTP has been sent to your email.')
                    except Exception:
                        messages.error(request, 'Could not send OTP. Please try again.')
                else:
                    messages.error(request, 'Your account has no email address set. Contact support.')
                return render(request, 'login.html', {'form': form})
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            otp_input = (form.cleaned_data.get('otp') or '').strip()

            # If OTP not provided yet, validate creds and send OTP
            if not otp_input:
                user = authenticate(request, username=username, password=password)
                if user is None:
                    messages.error(request, 'Invalid username or password.')
                else:
                    # Generate a simple 4-digit OTP and store in session for this username
                    import random
                    otp_code = f"{random.randint(1000, 9999)}"
                    request.session['login_username'] = username
                    request.session['login_otp'] = otp_code
                    request.session.modified = True
                    # Try emailing the OTP if user has email
                    try:
                        recipient = getattr(user, 'email', '') or ''
                        if recipient:
                            send_mail(
                                subject='Your Login OTP',
                                message=f'Hello, thanks for selecting our shop.\nHere is your OTP: {otp_code}\nThank you — HAPPY SHOPPINGGGG',
                                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                                recipient_list=[recipient],
                                fail_silently=False,
                            )
                        # Always inform user that OTP was sent (or generated)
                        messages.info(request, 'OTP has been sent to your registered email. Enter it to proceed.')
                    except Exception:
                        # As a fallback, still allow entering the OTP; optionally could reveal in DEBUG
                        messages.info(request, 'Enter the OTP to proceed.')
                # Re-render form to accept OTP
                return render(request, 'login.html', {'form': form})

            # OTP provided: verify against session
            session_username = request.session.get('login_username')
            session_otp = request.session.get('login_otp')
            if session_username != username or not session_otp:
                messages.error(request, 'OTP session expired. Please try logging in again.')
                return redirect('login')
            if otp_input != session_otp:
                messages.error(request, 'Invalid OTP. Please try again.')
                return render(request, 'login.html', {'form': form})

            # OTP valid -> authenticate and login
            user = authenticate(request, username=username, password=password)
            if user is None:
                messages.error(request, 'Invalid username or password.')
                return render(request, 'login.html', {'form': form})
            login(request, user)
            # clear OTP session
            for k in ('login_username', 'login_otp'):
                if k in request.session:
                    del request.session[k]
            request.session.modified = True
            messages.success(request, 'Logged in successfully.')
            return redirect('/')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})


def logout_view(request):
    logout(request)
    messages.info(request, 'Logged out.')
    return redirect('/')


def order_success(request):
    return render(request, 'order_success.html')


@login_required
def profile(request):
    return render(request, 'profile.html')

# Create your views here.
