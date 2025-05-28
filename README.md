# Electronics Store

An e-commerce platform for electronics similar to DNS Shop.

## Features

- Product catalog with categories and brands
- Product specifications and images
- User authentication and authorization
- Shopping cart and order management
- Admin panel for product management

## Tech Stack

- Backend: FastAPI (Python)
- Database: PostgreSQL
- Frontend: React (coming soon)
- ORM: SQLAlchemy
- Authentication: JWT

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a .env file in the root directory with the following content:
```
DATABASE_URL=postgresql://user:password@localhost/electronics_store
SECRET_KEY=your-secret-key-here
```

4. Initialize the database:
```bash
alembic upgrade head
```

5. Run the development server:
```bash
uvicorn app.main:app --reload
```

The API will be available at http://localhost:8000

## API Documentation

Once the server is running, you can access the API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
app/
├── models.py          # Database models
├── database.py        # Database configuration
├── schemas.py         # Pydantic models
├── crud.py           # CRUD operations
├── api/              # API endpoints
│   ├── v1/
│   │   ├── endpoints/
│   │   │   ├── products.py
│   │   │   ├── categories.py
│   │   │   ├── brands.py
│   │   │   ├── users.py
│   │   │   └── orders.py
│   │   └── api.py
└── main.py           # FastAPI application
``` 