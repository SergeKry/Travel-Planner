# Travel Planner API

A Django REST Framework application for managing travel projects and artwork collections from the Art Institute of Chicago API.

## Features

- Project management with artwork collections
- Integration with Art Institute of Chicago API
- Track visited/unvisited artworks
- Project completion tracking
- RESTful API endpoints

## Prerequisites

- Python 3.8+
- pip
- virtualenv

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd Travel-Planner
```

### 2. Create and Activate Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```


### 4. Database Setup

Run migrations to create the database schema:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Running the Application

### Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### API Endpoints

- `GET /api/docs/` - Swagger API docs

## API Usage Examples

### Create a Project

```bash
curl -X POST http://localhost:8000/api/projects/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Art Tour",
    "description": "A tour of famous artworks",
    "start_date": "2026-02-04",
    "artwork_ids": [4, 129884, 999]
  }'
```

### Add Artwork to Project

```bash
curl -X POST http://localhost:8000/api/projects/1/artworks/ \
  -H "Content-Type: application/json" \
  -d '{"artwork_id": 12345}'
```

### Update Artwork Visit Status

```bash
curl -X PATCH http://localhost:8000/api/projects/1/artworks/12345/ \
  -H "Content-Type: application/json" \
  -d '{"visited": true, "notes": "Beautiful painting!"}'
```

## Development

### Code Style

This project follows PEP 8 style guidelines. Use tools like `flake8` or `black` for code formatting.

### Project Structure

```
Travel-Planner/
├── api/                    # Main application
│   ├── models.py          # Database models
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── urls.py            # URL routing
│   ├── services.py        # Business logic
│   └── utils.py           # Utility functions
├── config/                # Django configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Dependencies

Key dependencies include:
- Django
- Django REST Framework
- requests (for API calls)

