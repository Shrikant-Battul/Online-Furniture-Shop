from .models import Category


def categories(request):
    try:
        cats = list(Category.objects.all().values_list('name', 'slug'))
    except Exception:
        cats = []
    if not cats:
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
    # Cart count from session
    cart = request.session.get('cart', {}) or {}
    cart_count = 0
    for entry in cart.values():
        try:
            cart_count += int(entry.get('qty', 0))
        except Exception:
            cart_count += 0
    return {"nav_categories": cats, "cart_count": cart_count}
