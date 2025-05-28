import os
from app.database import engine
from app.models import Base
from app.seed_data import seed_database

def init_db():
    # Создаем все таблицы
    Base.metadata.create_all(bind=engine)
    
    # Заполняем базу данных тестовыми данными
    seed_database()

if __name__ == "__main__":
    init_db() 