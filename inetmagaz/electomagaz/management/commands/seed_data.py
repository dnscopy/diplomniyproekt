from django.core.management.base import BaseCommand
from ...models import Category, Brand, Product, ProductSpecification, ProductImage, User
import random

class Command(BaseCommand):
    help = 'Заполняет базу данных большим количеством тестовых данных'

    def handle(self, *args, **kwargs):
        # Очистка всех связанных таблиц (сначала дочерние, потом родительские)
        ProductImage.objects.all().delete()
        ProductSpecification.objects.all().delete()
        Product.objects.all().delete()
        Category.objects.all().delete()
        Brand.objects.all().delete()

        # Категории
        categories_data = [
            {
                "name": "Компьютеры и ноутбуки",
                "description": "Компьютеры, ноутбуки и комплектующие",
                "subcategories": [
                    {"name": "Ноутбуки", "description": "Портативные компьютеры"},
                    {"name": "Системные блоки", "description": "Стационарные компьютеры"},
                    {"name": "Мониторы", "description": "Мониторы и дисплеи"},
                    {"name": "Комплектующие", "description": "Комплектующие для ПК"},
                ]
            },
            {
                "name": "Смартфоны и гаджеты",
                "description": "Смартфоны, планшеты и аксессуары",
                "subcategories": [
                    {"name": "Смартфоны", "description": "Мобильные телефоны"},
                    {"name": "Планшеты", "description": "Планшетные компьютеры"},
                    {"name": "Умные часы", "description": "Смарт-часы и фитнес-браслеты"},
                ]
            },
            {
                "name": "Аудио и видео",
                "description": "Аудио и видео техника",
                "subcategories": [
                    {"name": "Наушники", "description": "Наушники и гарнитуры"},
                    {"name": "Колонки", "description": "Акустические системы"},
                    {"name": "Телевизоры", "description": "Телевизоры и медиаплееры"},
                ]
            },
            {
                "name": "Бытовая техника",
                "description": "Техника для дома",
                "subcategories": [
                    {"name": "Кухонная техника", "description": "Техника для кухни"},
                    {"name": "Климатическая техника", "description": "Кондиционеры и обогреватели"},
                    {"name": "Уход за домом", "description": "Пылесосы и утюги"},
                ]
            },
            {
                "name": "Фото и видеотехника",
                "description": "Фотоаппараты, видеокамеры и аксессуары",
                "subcategories": [
                    {"name": "Фотоаппараты", "description": "Цифровые фотоаппараты"},
                    {"name": "Видеокамеры", "description": "Видеокамеры и экшн-камеры"},
                    {"name": "Объективы", "description": "Объективы для камер"},
                ]
            },
            {
                "name": "Игровая техника",
                "description": "Игровые приставки и аксессуары",
                "subcategories": [
                    {"name": "Игровые приставки", "description": "Консоли и аксессуары"},
                    {"name": "Игровые аксессуары", "description": "Геймпады, рули, VR"},
                ]
            }
        ]

        # Бренды (расширено)
        brands_data = [
            {"name": "Apple", "description": "Американская корпорация"},
            {"name": "Samsung", "description": "Южнокорейская компания"},
            {"name": "Sony", "description": "Японская корпорация"},
            {"name": "LG", "description": "Южнокорейская компания"},
            {"name": "Asus", "description": "Тайваньская компания"},
            {"name": "Lenovo", "description": "Китайская компания"},
            {"name": "Dell", "description": "Американская компания"},
            {"name": "HP", "description": "Американская компания"},
            {"name": "Bosch", "description": "Немецкая компания"},
            {"name": "Philips", "description": "Нидерландская компания"},
            {"name": "Canon", "description": "Японская компания"},
            {"name": "Nikon", "description": "Японская компания"},
            {"name": "Microsoft", "description": "Американская компания"},
            {"name": "Acer", "description": "Тайваньская компания"},
            {"name": "MSI", "description": "Тайваньская компания"},
            {"name": "Panasonic", "description": "Японская компания"},
            {"name": "Xiaomi", "description": "Китайская компания"},
            {"name": "Huawei", "description": "Китайская компания"},
            {"name": "JBL", "description": "Американская компания"},
            {"name": "Razer", "description": "Американская компания"},
        ]

        # Создание категорий
        category_objs = {}
        for category_data in categories_data:
            main_category = Category.objects.create(
                name=category_data["name"],
                description=category_data["description"]
            )
            category_objs[main_category.name] = main_category
            for subcategory_data in category_data["subcategories"]:
                sub = Category.objects.create(
                    name=subcategory_data["name"],
                    description=subcategory_data["description"],
                    parent=main_category
                )
                category_objs[sub.name] = sub

        # Создание брендов
        brand_objs = {}
        for brand_data in brands_data:
            brand = Brand.objects.create(**brand_data)
            brand_objs[brand.name] = brand

        # Характеристики для фильтрации
        spec_options = {
            "Процессор": ["Intel i5", "Intel i7", "AMD Ryzen 5", "Apple M2", "Snapdragon 8 Gen 2", "Apple M1 Pro", "MediaTek", "Exynos", "Apple A15", "Qualcomm 888"],
            "Оперативная память": ["4 ГБ", "6 ГБ", "8 ГБ", "12 ГБ", "16 ГБ", "32 ГБ"],
            "Память": ["64 ГБ", "128 ГБ", "256 ГБ", "512 ГБ", "1 ТБ"],
            "Диагональ экрана": ["5.5 дюймов", "6.1 дюймов", "6.5 дюймов", "13 дюймов", "14 дюймов", "15 дюймов", "17 дюймов", "24 дюйма", "27 дюймов", "55 дюймов"],
            "Цвет": ["Черный", "Белый", "Серый", "Синий", "Красный", "Зеленый", "Желтый"],
            "Тип": ["Беспроводные", "Проводные", "Гарнитура", "Моноблок", "Стационарный", "Портативный"],
            "Камера": ["12 Мп", "48 Мп", "64 Мп", "108 Мп", "Нет"],
            "HDR": ["Есть", "Нет", "Dolby Vision"],
            "Частота обновления": ["60 Гц", "90 Гц", "120 Гц"],
        }

        # Генерация большого количества товаров с разными характеристиками
        product_names = [
            "ProBook", "UltraVision", "MegaSound", "SmartClean", "PowerBox", "GameMaster", "PhotoPro", "VisionX", "SoundMax", "HomeGuard",
            "EcoCook", "SpeedDrive", "AirCooler", "LightPro", "EasyPrint", "SmartWatch", "FitBand", "UltraTab", "NoteX", "PixelCam"
        ]
        categories_list = list(category_objs.values())
        brands_list = list(brand_objs.values())
        spec_keys = list(spec_options.keys())
        for i in range(200):
            name = random.choice(product_names) + f" {random.randint(100,999)}"
            description = f"Описание для {name}"
            price = random.randint(3000, 250000)
            stock = random.randint(1, 200)
            brand = random.choice(brands_list)
            category = random.choice(categories_list)
            product = Product.objects.create(
                name=name,
                description=description,
                price=price,
                stock=stock,
                brand=brand,
                category=category
            )
            # Для каждого товара случайный набор характеристик
            for spec_name in random.sample(spec_keys, k=random.randint(3, 6)):
                ProductSpecification.objects.create(
                    product=product,
                    name=spec_name,
                    value=random.choice(spec_options[spec_name])
                )
            ProductImage.objects.create(
                product=product,
                image_url=f"/images/products/{product.id}.jpg",
                is_primary=True
            )

        # Пользователи
        if not User.objects.filter(email='admin@site.ru').exists():
            User.objects.create_superuser(email='admin@site.ru', username='admin', password='adminpass', role='admin')
        if not User.objects.filter(email='staff@site.ru').exists():
            User.objects.create_user(email='staff@site.ru', username='staff', password='staffpass', role='staff')
        if not User.objects.filter(email='customer@site.ru').exists():
            User.objects.create_user(email='customer@site.ru', username='customer', password='customerpass', role='customer')

        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена большим количеством тестовых данных!')) 