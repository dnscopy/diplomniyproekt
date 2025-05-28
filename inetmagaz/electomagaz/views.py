from django.shortcuts import render, redirect, get_object_or_404
from .models import Category, Product, Brand, ProductSpecification, User, ProductImage
from django.db.models import Min, Max, Count
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

# Create your views here.

def get_item(dictionary, key):
    return dictionary.get(key, [])

def catalog(request):
    categories = Category.objects.filter(parent__isnull=True)
    all_categories = Category.objects.all()
    products_queryset = Product.objects.all()
    brands = Brand.objects.all()

    # Поиск и фильтрация
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category', '')
    brand_ids = request.GET.getlist('brand')
    price_min = request.GET.get('price_min', '')
    price_max = request.GET.get('price_max', '')

    # Фильтрация по характеристикам
    spec_filters = {}
    for key, value in request.GET.items():
        if key.startswith('spec_') and value:
            spec_filters[key[5:]] = value if isinstance(value, list) else [value]

    if query:
        products_queryset = products_queryset.filter(name__icontains=query)
    if category_id:
        products_queryset = products_queryset.filter(category_id=category_id)
    if brand_ids:
        products_queryset = products_queryset.filter(brand_id__in=brand_ids)
    if price_min:
        products_queryset = products_queryset.filter(price__gte=price_min)
    if price_max:
        products_queryset = products_queryset.filter(price__lte=price_max)

    # Фильтрация по характеристикам (AND по каждому фильтру)
    for spec_name, values in spec_filters.items():
        products_queryset = products_queryset.filter(specifications__name=spec_name, specifications__value__in=values)

    # Ensure distinct products to avoid duplicates
    products_queryset = products_queryset.distinct()

    # Для фильтров: собираем все уникальные значения характеристик среди товаров
    specs_qs = ProductSpecification.objects.filter(product__in=products_queryset)
    spec_names = specs_qs.values_list('name', flat=True).distinct()
    spec_values = {}
    for name in spec_names:
        spec_values[name] = specs_qs.filter(name=name).values_list('value', flat=True).distinct()

    # Для фильтра по цене
    price_range = products_queryset.aggregate(min=Min('price'), max=Max('price'))

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(products_queryset, 20)  # Show 20 products per page
    
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        products = paginator.page(1)
    except EmptyPage:
        products = paginator.page(paginator.num_pages)

    return render(request, 'catalog.html', {
        'categories': categories,
        'products': products,
        'all_categories': all_categories,
        'brands': brands,
        'selected_category': category_id,
        'selected_brands': brand_ids,
        'query': query,
        'spec_values': spec_values,
        'spec_filters': spec_filters,
        'price_min': price_min,
        'price_max': price_max,
        'price_range': price_range,
        'get_item': get_item,
    })

def stub(request, page_title):
    return render(request, 'stub.html', {'page_title': page_title})

# Страницы-заглушки
@require_GET
def brands(request):
    brands = Brand.objects.all()
    return render(request, 'brands.html', {'brands': brands})

@require_GET
def promotions(request):
    return stub(request, 'Акции')

@require_GET
def delivery(request):
    return stub(request, 'Доставка')

@require_GET
def contacts(request):
    return render(request, 'contacts.html')

@require_GET
def cart(request):
    cart = request.session.get('cart', {})
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids).prefetch_related('images')
    cart_items = []
    total = 0
    for product in products:
        qty = cart.get(str(product.id), 0)
        subtotal = product.price * qty
        total += subtotal
        cart_items.append({
            'product': product,
            'qty': qty,
            'subtotal': subtotal,
        })
    return render(request, 'cart.html', {'cart_items': cart_items, 'total': total})

@require_GET
def favorites(request):
    favorite_ids = request.session.get('favorites', [])
    favorite_products = Product.objects.filter(id__in=favorite_ids).prefetch_related('images')
    return render(request, 'favorites.html', {
        'favorite_products': favorite_products,
        'favorites_count': len(favorite_ids)
    })

@require_GET
def compare(request):
    compare_ids = request.session.get('compare', [])
    products = Product.objects.filter(id__in=compare_ids).prefetch_related('images', 'specifications')
    
    # Если есть товары для сравнения, собираем все их спецификации
    all_specs = {}
    if products:
        for product in products:
            specs = product.specifications.all()
            for spec in specs:
                if spec.name not in all_specs:
                    all_specs[spec.name] = []
                all_specs[spec.name].append(spec.value)
    
    return render(request, 'compare.html', {
        'products': products,
        'all_specs': all_specs,
        'compare_count': len(compare_ids)
    })

def redirect_by_role(user):
    if user.role == 'admin':
        return redirect('/adminpanel')
    elif user.role == 'staff':
        return redirect('/staff')
    else:
        return redirect('/catalog')

@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect_by_role(user)
        else:
            messages.error(request, "Неверный email или пароль.")
    return render(request, "login.html")

@require_http_methods(["GET", "POST"])
def register(request):
    if request.method == "POST":
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        username = request.POST.get("username")
        full_name = request.POST.get("full_name")
        password = request.POST.get("password")
        role = request.POST.get("role")
        if not email and not phone:
            messages.error(request, "Укажите email или телефон.")
        elif not username:
            messages.error(request, "Укажите никнейм.")
        elif not password:
            messages.error(request, "Укажите пароль.")
        elif role not in ["staff", "customer"]:
            messages.error(request, "Выберите роль.")
        else:
            try:
                user = User.objects.create_user(
                    email=email if email else None,
                    phone=phone if phone else None,
                    username=username,
                    full_name=full_name,
                    password=password,
                    role=role
                )
                user.save()
                user = authenticate(request, email=email, password=password) if email else authenticate(request, username=username, password=password)
                if user:
                    auth_login(request, user)
                    return redirect_by_role(user)
                else:
                    messages.error(request, "Ошибка авторизации после регистрации.")
            except IntegrityError:
                messages.error(request, "Пользователь с таким email, телефоном или ником уже существует.")
    return render(request, "register.html")

@login_required
def profile(request):
    user = request.user
    return render(request, "profile.html", {"user": user})

@require_GET
def orders(request):
    # If the user is not logged in, redirect to login page
    if not request.user.is_authenticated:
        return redirect('/login?next=/orders')
    
    # Get orders from session (temporary solution)
    orders = request.session.get('orders', [])
    
    # Sort orders by created_at (newest first)
    orders = sorted(orders, key=lambda x: x.get('created_at', ''), reverse=True)
    
    return render(request, 'orders.html', {'orders': orders})

@require_GET
def checkout(request):
    cart = request.session.get('cart', {})
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids).prefetch_related('images')
    cart_items = []
    total = 0
    for product in products:
        qty = cart.get(str(product.id), 0)
        subtotal = product.price * qty
        total += subtotal
        cart_items.append({
            'product': product,
            'qty': qty,
            'subtotal': subtotal,
        })
    return render(request, 'checkout.html', {'cart_items': cart_items, 'total': total})

@require_POST
def place_order(request):
    # Here you would typically:
    # 1. Validate the order data
    # 2. Create an order record in the database
    # 3. Clear the cart
    # 4. Show a confirmation page
    
    # For now, just store the order details in session
    cart = request.session.get('cart', {})
    
    if not cart:
        return redirect('/cart/')
    
    # Get form data
    fullname = request.POST.get('fullname')
    email = request.POST.get('email')
    phone = request.POST.get('phone')
    address = request.POST.get('address')
    city = request.POST.get('city')
    postal_code = request.POST.get('postal_code')
    comment = request.POST.get('comment', '')
    payment_method = request.POST.get('payment_method')
    
    # Calculate order total from cart items
    product_ids = list(cart.keys())
    products = Product.objects.filter(id__in=product_ids)
    
    # Store order in session for display
    import datetime
    import random
    
    order_id = random.randint(10000, 99999)
    order_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Create new order in session if no orders exist
    if 'orders' not in request.session:
        request.session['orders'] = []
    
    # Add new order to session
    order = {
        'id': order_id,
        'created_at': order_date,
        'status': 'processing',
        'fullname': fullname,
        'email': email,
        'phone': phone,
        'address': address,
        'city': city,
        'postal_code': postal_code,
        'comment': comment,
        'payment_method': payment_method,
        'items': [],
        'subtotal': 0,
        'shipping': 300,
        'discount': 0,
        'total': 0
    }
    
    # Add items and calculate totals
    subtotal = 0
    for product in products:
        # Convert Decimal to float to ensure JSON serialization works
        price = float(product.price)
        quantity = int(cart.get(str(product.id), 0))
        item_total = price * quantity
        subtotal += item_total
        
        order['items'].append({
            'product_id': product.id,
            'product_name': product.name,
            'brand_name': product.brand.name,
            'price': price,
            'quantity': quantity
        })
    
    order['subtotal'] = subtotal
    order['total'] = subtotal + order['shipping'] - order['discount']
    
    # Add to orders list
    orders = request.session['orders']
    orders.append(order)
    request.session['orders'] = orders
    
    # Clear the cart
    request.session['cart'] = {}
    
    messages.success(request, 'Ваш заказ успешно оформлен! В ближайшее время с вами свяжется наш менеджер.')
    return redirect('/orders')

@require_GET
def about(request):
    return render(request, 'about.html')

@require_GET
def career(request):
    return stub(request, 'Вакансии')

@require_GET
def news(request):
    return stub(request, 'Новости')

@require_GET
def payment(request):
    return stub(request, 'Оплата')

@require_GET
def warranty(request):
    return stub(request, 'Гарантия')

@require_GET
def returns(request):
    return stub(request, 'Возврат')

@require_GET
def feedback(request):
    return stub(request, 'Обратная связь')

@require_GET
def shops(request):
    return stub(request, 'Наши магазины')

@login_required
def staff_dashboard(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    from .models import Product, Brand, Category
    products_count = Product.objects.count()
    brands_count = Brand.objects.count()
    categories_count = Category.objects.count()
    last_products = Product.objects.order_by('-created_at')[:10]
    return render(request, "staff_dashboard.html", {
        "user": request.user,
        "products_count": products_count,
        "brands_count": brands_count,
        "categories_count": categories_count,
        "last_products": last_products,
    })

@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return HttpResponseForbidden('Доступ только для админов')
    return render(request, "admin_dashboard.html", {"user": request.user})

def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    specs = product.specifications.all()
    images = product.images.all()
    return render(request, "product_detail.html", {"product": product, "specs": specs, "images": images})

@require_POST
def cart_add(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return redirect('/cart/')
    cart = request.session.get('cart', {})
    cart[product_id] = cart.get(product_id, 0) + 1
    request.session['cart'] = cart
    return redirect('/cart/')

@require_POST
def logout_view(request):
    logout(request)
    return redirect('/catalog')

@login_required
def staff_products(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    # Get all products with related data
    products = Product.objects.select_related('category', 'brand').all()
    
    # Apply filters
    search = request.GET.get('search', '')
    category_id = request.GET.get('category', '')
    brand_id = request.GET.get('brand', '')
    sort = request.GET.get('sort', '-created_at')
    
    if search:
        products = products.filter(name__icontains=search)
    if category_id:
        products = products.filter(category_id=category_id)
    if brand_id:
        products = products.filter(brand_id=brand_id)
    
    # Apply sorting
    if sort:
        products = products.order_by(sort)
    
    # Get all categories and brands for filters
    categories = Category.objects.all()
    brands = Brand.objects.all()
    
    # Pagination
    paginator = Paginator(products, 20)  # Show 20 products per page
    page = request.GET.get('page')
    products = paginator.get_page(page)
    
    return render(request, 'staff_products.html', {
        'products': products,
        'categories': categories,
        'brands': brands,
    })

@login_required
def staff_product_add(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    if request.method == 'POST':
        try:
            # Create product
            product = Product.objects.create(
                name=request.POST['name'],
                category_id=request.POST['category'],
                brand_id=request.POST['brand'],
                price=request.POST['price'],
                description=request.POST.get('description', '')
            )
            
            # Add specifications
            spec_names = request.POST.getlist('spec_names[]')
            spec_values = request.POST.getlist('spec_values[]')
            for name, value in zip(spec_names, spec_values):
                if name and value:  # Only add if both fields are filled
                    ProductSpecification.objects.create(
                        product=product,
                        name=name,
                        value=value
                    )
            
            # Handle images
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(product=product, image=image)
            
            messages.success(request, 'Товар успешно добавлен')
            return redirect('staff_products')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении товара: {str(e)}')
    
    return render(request, 'staff_product_add.html', {
        'categories': Category.objects.all(),
        'brands': Brand.objects.all()
    })

@login_required
def staff_product_edit(request, product_id):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            # Update product
            product.name = request.POST['name']
            product.category_id = request.POST['category']
            product.brand_id = request.POST['brand']
            product.price = request.POST['price']
            product.description = request.POST.get('description', '')
            product.save()
            
            # Update specifications
            product.specifications.all().delete()  # Remove old specs
            spec_names = request.POST.getlist('spec_names[]')
            spec_values = request.POST.getlist('spec_values[]')
            for name, value in zip(spec_names, spec_values):
                if name and value:  # Only add if both fields are filled
                    ProductSpecification.objects.create(
                        product=product,
                        name=name,
                        value=value
                    )
            
            # Handle new images
            images = request.FILES.getlist('images')
            for image in images:
                ProductImage.objects.create(product=product, image=image)
            
            messages.success(request, 'Товар успешно обновлен')
            return redirect('staff_products')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении товара: {str(e)}')
    
    return render(request, 'staff_product_add.html', {
        'product': product,
        'categories': Category.objects.all(),
        'brands': Brand.objects.all()
    })

@login_required
def staff_product_delete(request, product_id):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        try:
            product.delete()
            messages.success(request, 'Товар успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении товара: {str(e)}')
    
    return redirect('staff_products')

@login_required
def staff_product_delete_image(request, image_id):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    image = get_object_or_404(ProductImage, id=image_id)
    product_id = image.product.id
    
    try:
        image.delete()
        messages.success(request, 'Изображение успешно удалено')
    except Exception as e:
        messages.error(request, f'Ошибка при удалении изображения: {str(e)}')
    
    return redirect('staff_product_edit', product_id=product_id)

@login_required
def staff_brands(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    # Get all brands with product count
    brands = Brand.objects.annotate(product_count=Count('products'))
    
    # Apply search filter
    search = request.GET.get('search', '')
    if search:
        brands = brands.filter(name__icontains=search)
    
    # Pagination
    paginator = Paginator(brands, 20)  # Show 20 brands per page
    page = request.GET.get('page')
    brands = paginator.get_page(page)
    
    return render(request, 'staff_brands.html', {
        'brands': brands
    })

@login_required
def staff_brand_add(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    if request.method == 'POST':
        try:
            brand = Brand.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', '')
            )
            
            # Handle logo upload
            if 'logo' in request.FILES:
                brand.logo = request.FILES['logo']
                brand.save()
            
            messages.success(request, 'Бренд успешно добавлен')
            return redirect('staff_brands')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении бренда: {str(e)}')
    
    return render(request, 'staff_brand_add.html')

@login_required
def staff_brand_edit(request, brand_id):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    brand = get_object_or_404(Brand, id=brand_id)
    
    if request.method == 'POST':
        try:
            brand.name = request.POST['name']
            brand.description = request.POST.get('description', '')
            
            # Handle logo upload
            if 'logo' in request.FILES:
                brand.logo = request.FILES['logo']
            
            brand.save()
            messages.success(request, 'Бренд успешно обновлен')
            return redirect('staff_brands')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении бренда: {str(e)}')
    
    return render(request, 'staff_brand_add.html', {
        'brand': brand
    })

@login_required
def staff_brand_delete(request, brand_id):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    brand = get_object_or_404(Brand, id=brand_id)
    
    if request.method == 'POST':
        try:
            brand.delete()
            messages.success(request, 'Бренд успешно удален')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении бренда: {str(e)}')
    
    return redirect('staff_brands')

@login_required
def staff_categories(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    # Get all categories with counts
    categories = Category.objects.annotate(
        product_count=Count('products'),
        subcategories_count=Count('subcategories')
    )
    
    # Apply search filter
    search = request.GET.get('search', '')
    if search:
        categories = categories.filter(name__icontains=search)
    
    # Pagination
    paginator = Paginator(categories, 20)  # Show 20 categories per page
    page = request.GET.get('page')
    categories = paginator.get_page(page)
    
    return render(request, 'staff_categories.html', {
        'categories': categories
    })

@login_required
def staff_category_add(request):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    if request.method == 'POST':
        try:
            category = Category.objects.create(
                name=request.POST['name'],
                description=request.POST.get('description', '')
            )
            
            # Set parent category if selected
            parent_id = request.POST.get('parent')
            if parent_id:
                category.parent_id = parent_id
                category.save()
            
            messages.success(request, 'Категория успешно добавлена')
            return redirect('staff_categories')
        except Exception as e:
            messages.error(request, f'Ошибка при добавлении категории: {str(e)}')
    
    return render(request, 'staff_category_add.html', {
        'categories': Category.objects.all()
    })

@login_required
def staff_category_edit(request, category_id):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            category.name = request.POST['name']
            category.description = request.POST.get('description', '')
            
            # Update parent category
            parent_id = request.POST.get('parent')
            if parent_id:
                category.parent_id = parent_id
            else:
                category.parent = None
            
            category.save()
            messages.success(request, 'Категория успешно обновлена')
            return redirect('staff_categories')
        except Exception as e:
            messages.error(request, f'Ошибка при обновлении категории: {str(e)}')
    
    return render(request, 'staff_category_add.html', {
        'category': category,
        'categories': Category.objects.all()
    })

@login_required
def staff_category_delete(request, category_id):
    if request.user.role != 'staff':
        return HttpResponseForbidden('Доступ только для сотрудников')
    
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        try:
            # Check if category has products or children
            if category.products.exists():
                messages.error(request, 'Нельзя удалить категорию, содержащую товары')
            elif category.children.exists():
                messages.error(request, 'Нельзя удалить категорию, содержащую подкатегории')
            else:
                category.delete()
                messages.success(request, 'Категория успешно удалена')
        except Exception as e:
            messages.error(request, f'Ошибка при удалении категории: {str(e)}')
    
    return redirect('staff_categories')

@require_POST
def cart_update(request):
    """Update the quantity of an item in the cart or remove it."""
    product_id = request.POST.get('product_id')
    action = request.POST.get('action')
    
    if not product_id or not action:
        return JsonResponse({'status': 'error', 'message': 'Missing required parameters'})
    
    cart = request.session.get('cart', {})
    
    if action == 'remove':
        if product_id in cart:
            del cart[product_id]
            request.session['cart'] = cart
            return JsonResponse({'status': 'success', 'message': 'Item removed from cart'})
    
    elif action == 'increase':
        cart[product_id] = cart.get(product_id, 0) + 1
        request.session['cart'] = cart
        return JsonResponse({'status': 'success', 'quantity': cart[product_id]})
    
    elif action == 'decrease':
        if product_id in cart:
            if cart[product_id] > 1:
                cart[product_id] -= 1
            else:
                del cart[product_id]
            request.session['cart'] = cart
            return JsonResponse({'status': 'success', 'quantity': cart.get(product_id, 0)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid action'})

@require_POST
def compare_add(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return redirect('catalog')
    
    # Получаем или создаем список сравнения в сессии
    compare_list = request.session.get('compare', [])
    
    # Проверяем, не превышает ли количество товаров лимит (например, 3)
    if product_id not in compare_list and len(compare_list) < 3:
        compare_list.append(product_id)
        request.session['compare'] = compare_list
        messages.success(request, 'Товар добавлен к сравнению')
    elif product_id in compare_list:
        messages.info(request, 'Этот товар уже в списке сравнения')
    else:
        messages.warning(request, 'Можно сравнивать не более 3 товаров')
    
    # Возвращаемся на предыдущую страницу
    next_url = request.POST.get('next', '/catalog')
    return redirect(next_url)

@require_POST
def compare_remove(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return redirect('compare')
    
    # Получаем список сравнения из сессии
    compare_list = request.session.get('compare', [])
    
    # Удаляем товар из списка
    if product_id in compare_list:
        compare_list.remove(product_id)
        request.session['compare'] = compare_list
        messages.success(request, 'Товар удален из сравнения')
    
    return redirect('compare')

@require_POST
def compare_clear(request):
    # Очищаем список сравнения
    request.session['compare'] = []
    messages.success(request, 'Список сравнения очищен')
    return redirect('compare')

@require_POST
def favorites_add(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return redirect('catalog')
    
    # Get or create favorites list in session
    favorites_list = request.session.get('favorites', [])
    
    # Add product to favorites if not already there
    if product_id not in favorites_list:
        favorites_list.append(product_id)
        request.session['favorites'] = favorites_list
        messages.success(request, 'Товар добавлен в избранное')
    else:
        messages.info(request, 'Этот товар уже в избранном')
    
    # Return to previous page
    next_url = request.POST.get('next', '/catalog')
    return redirect(next_url)

@require_POST
def favorites_remove(request):
    product_id = request.POST.get('product_id')
    if not product_id:
        return redirect('favorites')
    
    # Get favorites list from session
    favorites_list = request.session.get('favorites', [])
    
    # Remove product from list
    if product_id in favorites_list:
        favorites_list.remove(product_id)
        request.session['favorites'] = favorites_list
        messages.success(request, 'Товар удален из избранного')
    
    return redirect('favorites')

@require_POST
def favorites_clear(request):
    # Clear favorites list
    request.session['favorites'] = []
    messages.success(request, 'Список избранного очищен')
    return redirect('favorites')
