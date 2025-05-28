# Импорты необходимых модулей
from django.urls import path
from . import views
from .admin_views import (
    AdminDashboardView, ProductAdminListView, ProductAdminUpdateView, ProductAdminDeleteView,
    CategoryAdminListView, CategoryAdminUpdateView, CategoryAdminDeleteView, CategoryAdminCreateView,
    OrderAdminListView, OrderAdminUpdateView, UserAdminListView, UserAdminUpdateView, UserAdminToggleView
)

# Определение URL-адресов приложения
urlpatterns = [
    # Основные URL-адреса
    path('', views.home, name='home'),  # Главная страница
    path('register/', views.register, name='register'),  # Регистрация
    path('login/', views.login_view, name='login'),  # Вход
    path('profile/', views.profile, name='profile'),  # Профиль пользователя
    path('profile/update/', views.profile_update, name='profile_update'),  # Обновление профиля
    
    # URL-адреса для работы с товарами
    path('products/', views.ProductListView.as_view(), name='product_list'),  # Список всех товаров
    path('products/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),  # Товары по категории
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),  # Детали категории
    
    # URL-адреса для работы с корзиной
    path('cart/', views.cart, name='cart'),  # Корзина
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),  # Добавление в корзину
    path('cart/remove/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),  # Удаление из корзины
    path('cart/decrease/<int:cart_item_id>/', views.decrease_cart_item, name='decrease_cart_item'),  # Уменьшение количества
    
    # URL-адреса для оформления заказа
    path('checkout/', views.checkout, name='checkout'),  # Оформление заказа
    path('create-order/', views.create_order, name='create_order'),  # Создание заказа
    path('order-success/<int:order_id>/', views.order_success, name='order_success'),  # Успешное оформление
    
    # Дополнительные URL-адреса
    path('search/', views.search, name='search'),  # Поиск товаров
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),  # Детали товара
    path('product/create/', views.ProductCreateView.as_view(), name='product_create'),  # Создание товара
    path('product/<int:pk>/update/', views.ProductUpdateView.as_view(), name='product_update'),  # Обновление товара
    path('order/<int:pk>/', views.order_detail, name='order_detail'),  # Детали заказа
    
    # URL-адреса для административной панели
    path('admin-dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),  # Панель администратора
    
    # Управление товарами в админке
    path('admin-dashboard/products/', ProductAdminListView.as_view(), name='admin_product_list'),  # Список товаров
    path('admin-dashboard/products/<int:pk>/update/', ProductAdminUpdateView.as_view(), name='admin_product_update'),  # Обновление товара
    path('admin-dashboard/products/<int:pk>/delete/', ProductAdminDeleteView.as_view(), name='admin_product_delete'),  # Удаление товара
    
    # Управление категориями в админке
    path('admin-dashboard/categories/', CategoryAdminListView.as_view(), name='admin_category_list'),  # Список категорий
    path('admin-dashboard/categories/create/', CategoryAdminCreateView.as_view(), name='admin_category_create'),  # Создание категории
    path('admin-dashboard/categories/<int:pk>/update/', CategoryAdminUpdateView.as_view(), name='admin_category_update'),  # Обновление категории
    path('admin-dashboard/categories/<int:pk>/delete/', CategoryAdminDeleteView.as_view(), name='admin_category_delete'),  # Удаление категории
    
    # Управление заказами в админке
    path('admin-dashboard/orders/', OrderAdminListView.as_view(), name='admin_order_list'),  # Список заказов
    path('admin-dashboard/orders/<int:pk>/update/', OrderAdminUpdateView.as_view(), name='admin_order_update'),  # Обновление заказа
    
    # Управление пользователями в админке
    path('admin-dashboard/users/', UserAdminListView.as_view(), name='admin_user_list'),  # Список пользователей
    path('admin-dashboard/users/<int:pk>/update/', UserAdminUpdateView.as_view(), name='admin_user_update'),  # Обновление пользователя
    path('admin-dashboard/users/<int:pk>/toggle/', UserAdminToggleView.as_view(), name='admin_user_toggle'),  # Включение/отключение пользователя
] 