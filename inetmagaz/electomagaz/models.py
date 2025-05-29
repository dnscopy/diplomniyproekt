# Модели для интернет-магазина ElectroMagaz
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

# Категории товаров (иерархия через parent)
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Название категории
    description = models.TextField(blank=True, null=True)  # Описание категории
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')  # Родительская категория (для вложенности)
    
    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
    
    def __str__(self):
        return self.name

# Модель бренда (производителя)
class Brand(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Название бренда
    description = models.TextField(blank=True, null=True)  # Описание бренда
    logo_url = models.URLField(blank=True, null=True)  # Ссылка на логотип
    
    class Meta:
        verbose_name = 'Бренд'
        verbose_name_plural = 'Бренды'
    
    def __str__(self):
        return self.name

# Модель товара
class Product(models.Model):
    name = models.CharField(max_length=200)  # Название товара
    description = models.TextField()  # Описание товара
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Цена товара
    stock = models.IntegerField(default=0)  # Количество на складе
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name='products')  # Бренд товара
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')  # Категория товара
    created_at = models.DateTimeField(default=timezone.now)  # Дата создания
    updated_at = models.DateTimeField(auto_now=True)  # Дата обновления
    is_active = models.BooleanField(default=True)  # Активен ли товар
    
    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
    
    def __str__(self):
        return self.name

# Изображения для товаров
class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')  # К какому товару относится
    image_url = models.URLField()  # Ссылка на изображение
    is_primary = models.BooleanField(default=False)  # Главное изображение?
    
    class Meta:
        verbose_name = 'Изображение товара'
        verbose_name_plural = 'Изображения товаров'
    
    def __str__(self):
        return f"Изображение {self.product.name}"

# Характеристики товара (например, цвет, размер)
class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')  # К какому товару относится
    name = models.CharField(max_length=100)  # Название характеристики
    value = models.CharField(max_length=200)  # Значение характеристики
    
    class Meta:
        verbose_name = 'Характеристика товара'
        verbose_name_plural = 'Характеристики товаров'
    
    def __str__(self):
        return f"{self.name}: {self.value}"

# Пользователь (расширяет стандартного пользователя Django)
class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Админ'),      # Администратор
        ('staff', 'Сотрудник'), # Сотрудник магазина
        ('customer', 'Покупатель'), # Покупатель
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')  # Роль пользователя
    email = models.EmailField(unique=True)  # Email (используется как логин)
    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)  # Телефон
    full_name = models.CharField(max_length=150, blank=True, null=True)  # ФИО

    USERNAME_FIELD = 'email'  # Авторизация по email
    REQUIRED_FIELDS = ['username']  # username обязателен для совместимости

    def __str__(self):
        return self.email
