# Импорты необходимых модулей
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator
from django.utils.text import slugify
import uuid

# Модель пользователя, расширяющая стандартную модель Django User
class User(AbstractUser):
    # Выбор роли пользователя в системе
    ROLE_CHOICES = (
        ('customer', 'Покупатель'),
        ('seller', 'Продавец'),
        ('admin', 'Администратор'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')  # Роль пользователя
    phone = models.CharField(max_length=15, blank=True)  # Номер телефона
    address = models.TextField(blank=True)  # Адрес пользователя
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)  # Аватар пользователя

# Модель категорий товаров
class Category(models.Model):
    name = models.CharField(max_length=100)  # Название категории
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')  # Родительская категория
    slug = models.SlugField(unique=True, blank=True)  # URL-слаг для категории

    def save(self, *args, **kwargs):
        # Автоматическое создание слага при сохранении
        if not self.slug:
            base_slug = slugify(self.name)
            if self.parent:
                base_slug = f"{slugify(self.parent.name)}-{base_slug}"
            
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent:
            return f"{self.parent.name} - {self.name}"
        return self.name

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

# Модель товара
class Product(models.Model):
    name = models.CharField(max_length=200)  # Название товара
    description = models.TextField()  # Описание товара
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])  # Цена товара
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')  # Категория товара
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='products')  # Продавец товара
    image = models.ImageField(upload_to='products/', blank=True, null=True)  # Изображение товара
    stock = models.PositiveIntegerField(default=0)  # Количество товара на складе
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания
    updated_at = models.DateTimeField(auto_now=True)  # Дата обновления
    is_active = models.BooleanField(default=True)  # Активен ли товар

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'

# Модель корзины
class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='cart')  # Пользователь
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Товар
    quantity = models.PositiveIntegerField(default=1)  # Количество товара
    created_at = models.DateTimeField(auto_now_add=True)  # Дата добавления в корзину

    @property
    def total_price(self):
        # Расчет общей стоимости товаров в корзине
        return self.quantity * self.product.price

    def __str__(self):
        return f"{self.user.username}'s cart - {self.product.name}"

    class Meta:
        verbose_name = 'Корзина'
        verbose_name_plural = 'Корзины'

# Модель заказа
class Order(models.Model):
    # Статусы заказа
    STATUS_CHOICES = (
        ('pending', 'В обработке'),
        ('processing', 'В процессе'),
        ('shipped', 'Отправлен'),
        ('delivered', 'Доставлен'),
        ('cancelled', 'Отменен'),
    )
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')  # Пользователь
    products = models.ManyToManyField(Product, through='OrderItem')  # Товары в заказе
    total_price = models.DecimalField(max_digits=10, decimal_places=2)  # Общая стоимость заказа
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')  # Статус заказа
    created_at = models.DateTimeField(auto_now_add=True)  # Дата создания заказа
    updated_at = models.DateTimeField(auto_now=True)  # Дата обновления заказа
    shipping_address = models.TextField()  # Адрес доставки
    phone = models.CharField(max_length=15)  # Телефон для связи

    def __str__(self):
        return f"Order {self.id} by {self.user.username}"

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

# Модель позиции заказа (связь между заказом и товаром)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)  # Заказ
    product = models.ForeignKey(Product, on_delete=models.CASCADE)  # Товар
    quantity = models.PositiveIntegerField()  # Количество товара
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена товара на момент заказа

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in order {self.order.id}"

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа' 