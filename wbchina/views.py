# Импорты необходимых модулей
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from .models import Product, Category, Cart, Order, User, OrderItem
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q
from wbchina.forms import ProfileUpdateForm

# Главная страница сайта - отображает категории и последние товары
def home(request):
    categories = Category.objects.filter(parent=None)  # Получаем все родительские категории
    products = Product.objects.filter(is_active=True)[:8]  # Получаем 8 активных товаров
    return render(request, 'home.html', {
        'categories': categories,
        'products': products
    })

# Страница детальной информации о категории - показывает товары и подкатегории
def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    # Получаем все товары из данной категории и её подкатегорий
    products = Product.objects.filter(
        Q(category=category) | Q(category__parent=category),
        is_active=True
    )
    subcategories = category.subcategories.all()  # Получаем все подкатегории
    
    return render(request, 'category_detail.html', {
        'category': category,
        'products': products,
        'subcategories': subcategories
    })

# Представление для отображения списка товаров с пагинацией
class ProductListView(ListView):
    model = Product
    template_name = 'wbchina/product_list.html'
    context_object_name = 'products'
    paginate_by = 12  # Пагинация по 12 товаров на странице

    def get_queryset(self):
        # Фильтрация товаров по категории, если указана
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            return Product.objects.filter(category=category, is_active=True)
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(parent=None)
        return context

# Представление для отображения детальной информации о товаре
class ProductDetailView(DetailView):
    model = Product
    template_name = 'wbchina/product_detail.html'
    context_object_name = 'product'

# Добавление товара в корзину (требуется авторизация)
@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    # Создаем или обновляем запись в корзине
    cart_item, created = Cart.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={'quantity': 1}
    )
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    messages.success(request, "Товар добавлен в корзину")
    return redirect('cart')

# Отображение корзины пользователя (требуется авторизация)
@login_required
def cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    cart_total = sum(item.total_price for item in cart_items)
    return render(request, 'wbchina/cart.html', {
        'cart_items': cart_items,
        'cart_total': cart_total
    })

# Профиль пользователя (требуется авторизация)
@login_required
def profile(request):
    user = request.user
    # Если пользователь продавец, показываем его товары
    if user.role == 'seller':
        products = Product.objects.filter(seller=user)
    else:
        products = None
    orders = Order.objects.filter(user=user)
    return render(request, 'wbchina/profile.html', {
        'user': user,
        'products': products,
        'orders': orders
    })

# Создание нового товара (только для продавцов)
class ProductCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Product
    template_name = 'wbchina/product_form.html'
    fields = ['name', 'description', 'price', 'category', 'image', 'stock']
    success_url = reverse_lazy('profile')

    def test_func(self):
        return self.request.user.role == 'seller'

    def form_valid(self, form):
        form.instance.seller = self.request.user
        return super().form_valid(form)

# Обновление информации о товаре (только для продавцов)
class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Product
    template_name = 'wbchina/product_form.html'
    fields = ['name', 'description', 'price', 'category', 'image', 'stock', 'is_active']
    success_url = reverse_lazy('profile')

    def test_func(self):
        product = self.get_object()
        return self.request.user == product.seller

# Регистрация нового пользователя
def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']
        role = request.POST['role']
        phone = request.POST.get('phone', '')
        address = request.POST.get('address', '')

        # Проверка паролей
        if password1 != password2:
            messages.error(request, 'Пароли не совпадают')
            return redirect('register')

        # Проверка существования пользователя
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Пользователь с таким именем уже существует')
            return redirect('register')

        # Создание пользователя
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password1,
            role=role,
            phone=phone,
            address=address
        )

        # Назначение прав администратора
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
            user.save()

        login(request, user)
        messages.success(request, 'Регистрация успешно завершена!')
        return redirect('home')

    return render(request, 'registration/register.html')

# Вход в систему
def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Вы успешно вошли в систему')
            return redirect('home')
        else:
            messages.error(request, 'Неверное имя пользователя или пароль')
    return render(request, 'registration/login.html')

# Удаление товара из корзины (требуется авторизация)
@login_required
def remove_from_cart(request, cart_item_id):
    Cart.objects.filter(id=cart_item_id, user=request.user).delete()
    messages.success(request, "Товар удален из корзины")
    return redirect('cart')

# Страница оформления заказа (требуется авторизация)
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.error(request, "Ваша корзина пуста")
        return redirect('cart')
    
    cart_total = sum(item.total_price for item in cart_items)
    return render(request, 'wbchina/checkout.html', {
        'cart_items': cart_items,
        'cart_total': cart_total
    })

# Создание нового заказа (требуется авторизация)
@login_required
def create_order(request):
    if request.method == 'POST':
        cart_items = Cart.objects.filter(user=request.user)
        if not cart_items.exists():
            messages.error(request, "Ваша корзина пуста")
            return redirect('cart')

        address = request.POST.get('address')
        phone = request.POST.get('phone')
        if not address or not phone:
            messages.error(request, "Пожалуйста, укажите адрес доставки и телефон")
            return redirect('checkout')

        total_price = sum(item.total_price for item in cart_items)
        
        # Создание заказа
        order = Order.objects.create(
            user=request.user,
            total_price=total_price,
            shipping_address=address,
            phone=phone
        )

        # Создание позиций заказа
        for cart_item in cart_items:
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        cart_items.delete()
        messages.success(request, "Заказ успешно оформлен!")
        return redirect('order_success', order_id=order.id)
    
    return redirect('checkout')

# Страница успешного оформления заказа (требуется авторизация)
@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'wbchina/order_success.html', {'order': order})

# Поиск товаров
def search(request):
    query = request.GET.get('q', '')
    if query:
        # Поиск по названию и описанию товара
        products = Product.objects.filter(
            Q(name__icontains=query) | Q(description__icontains=query),
            is_active=True
        )
    else:
        products = []
    return render(request, 'search.html', {
        'products': products,
        'query': query
    })

# Уменьшение количества товара в корзине (требуется авторизация)
@login_required
def decrease_cart_item(request, cart_item_id):
    cart_item = get_object_or_404(Cart, id=cart_item_id, user=request.user)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
        messages.success(request, "Количество товара уменьшено")
    else:
        cart_item.delete()
        messages.success(request, "Товар удален из корзины")
    return redirect('cart')

# Обновление профиля пользователя (требуется авторизация)
@login_required
def profile_update(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль успешно обновлен')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    
    return render(request, 'wbchina/profile_update.html', {'form': form})

# Детальная информация о заказе (требуется авторизация)
@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'wbchina/order_detail.html', {'order': order})

# Выход из системы
def custom_logout(request):
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home') 