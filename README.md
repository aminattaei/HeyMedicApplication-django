<<<<<<< HEAD
# HeyMedic

HeyMedic is a Django-based healthcare platform connecting patients and doctors in Iran. It supports phone-number authentication, role-based access (admin, patient, doctor), appointment booking, online payments, patient reviews, and a fully responsive frontend.

## Features

### Implemented

- **Custom user model** — Phone number as the primary login identifier (Iran region)
- **Role-based users** — Admin, Patient, and Doctor roles with `is_verified` flag
- **Django Admin** — Customized user management for all models
- **Appointments** — TimeSlot management (doctor), appointment booking (patient), cancellation
- **Payments** — Payment initialization and verification (gateway-ready)
- **Reviews** — Patient reviews with automatic doctor rating recalculation
- **JWT Authentication** — Token-based auth via SimpleJWT + Djoser
- **REST API** — Full CRUD APIs for all apps with OpenAPI/Swagger documentation
- **Frontend** — Responsive RTL website with Tailwind CSS (CDN), Class-Based Views
- **Docker support** — PostgreSQL + Django via Docker Compose

### Frontend Pages

| Page | Description |
|------|-------------|
| Landing page | Hero section, features, call-to-action |
| Doctor list | Search and filter by specialty |
| Doctor profile | View details, available slots, book appointment |
| My appointments | Patient appointment list with cancel option |
| Doctor dashboard | Manage time slots, view appointments |
| Login / Register | Phone-number based authentication |

### Planned

| Feature | Technology |
|---------|------------|
| Chat | WebSocket + Django Channels |
| Video calls | Jitsi integration |
| Payment gateway | Zibal / IDPay / Mellat |
| Email verification | Celery + Redis |

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Django 6.0, Python 3.12 |
| API | Django REST Framework, SimpleJWT, Djoser, drf-spectacular |
| Database | PostgreSQL (Docker) or SQLite (local dev) |
| Auth | Custom user model, phone-number login, JWT tokens |
| Frontend | HTML, Tailwind CSS (CDN), vanilla JavaScript |
| Async tasks | Celery, Redis, django-celery-results |
| Deployment | Gunicorn, Docker Compose |
| Dev tools | pytest, pytest-django, black, flake8, Faker |

## Project Structure

```
HeyMdicApplication/
├── core/                          # Django project root
│   ├── core/                      # Settings, URLs, WSGI/ASGI
│   ├── accounts/                  # Custom User model and admin
│   ├── appointments/              # TimeSlot + Appointment models, API
│   ├── payments/                  # Payment model, API
│   ├── reviews/                   # Review model, API
│   ├── website/                   # Frontend (CBVs, templates, static)
│   │   ├── templates/website/     # HTML templates (RTL, Tailwind)
│   │   └── static/website/        # CSS, JS files
│   └── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.12+
- pip
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/)
- PostgreSQL 17 (via Docker)

## Environment Variables

Create a `.env` file in the project root:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database — SQLite for local dev
DATABASE_ENGINE=sqlite3
DATABASE_NAME=db.sqlite3

# Database — PostgreSQL with Docker
# DATABASE_ENGINE=postgresql
# DATABASE_NAME=heymedic
# DATABASE_USERNAME=heymedic
# DATABASE_PASSWORD=your-password
# DATABASE_HOST=db
# DATABASE_PORT=5432
```

| Variable | Description | Default |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | `fallback-secret-key` |
| `DEBUG` | Enable debug mode | `True` |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `backend` |
| `DATABASE_ENGINE` | `sqlite3` or `postgresql` | — |
| `DATABASE_NAME` | Database name or SQLite file path | `db.sqlite3` |
| `DATABASE_USERNAME` | PostgreSQL username | — |
| `DATABASE_PASSWORD` | PostgreSQL password | — |
| `DATABASE_HOST` | PostgreSQL host | `localhost` |
| `DATABASE_PORT` | PostgreSQL port | `5432` |

## Getting Started

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd HeyMdicApplication

# Create .env with PostgreSQL settings (see Environment Variables)

# Build and start services
docker compose up --build

# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser
```

Backend: [http://localhost:8000/](http://localhost:8000/)
Admin: [http://localhost:8000/admin/](http://localhost:8000/admin/)
Swagger: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

### Option 2: Local development (virtual environment)

```bash
# Clone the repository
git clone <repository-url>
cd HeyMdicApplication

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file (see Environment Variables)

# Run migrations
cd core
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

## API Endpoints

All APIs are available under `/api/v1/`:

| Endpoint | Methods | Description |
|----------|---------|-------------|
| `/api/v1/appointments/slots/` | GET, POST | List/create time slots |
| `/api/v1/appointments/appointments/` | GET, POST | List/create appointments |
| `/api/v1/appointments/appointments/{id}/book/` | POST | Book an appointment |
| `/api/v1/appointments/appointments/{id}/cancel/` | POST | Cancel an appointment |
| `/api/v1/payments/` | GET, POST | List/create payments |
| `/api/v1/payments/{id}/init_payment/` | POST | Initialize payment |
| `/api/v1/payments/{id}/verify_payment/` | POST | Verify payment |
| `/api/v1/reviews/` | GET, POST | List/create reviews |
| `/api/auth/jwt/create/` | POST | Login (get JWT tokens) |
| `/api/auth/jwt/refresh/` | POST | Refresh access token |
| `/api/auth/users/` | POST | Register new user |

### Authentication

```bash
# Login
curl -X POST http://localhost:8000/api/auth/jwt/create/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+989123456789", "password": "yourpassword"}'

# Use token in requests
curl http://localhost:8000/api/v1/appointments/appointments/ \
  -H "Authorization: Bearer <access_token>"
```

## User Model

| Field | Description |
|-------|-------------|
| `phone_number` | Unique identifier for login (`USERNAME_FIELD`) |
| `email` | Optional, unique email address |
| `role` | `admin`, `patient`, or `doctor` |
| `is_verified` | Whether the account has been verified |
| `created_at` | Account creation timestamp |

## Development

### Running tests

```bash
cd core
pytest
```

### Code formatting and linting

```bash
black .
flake8
```

### Static and media files

```bash
python manage.py collectstatic
```

## Architecture Notes

- **Appointments → Payments → Reviews** implementation order (each depends on the prior)
- **TimeSlot → Appointment** is OneToOne (one slot = one appointment)
- `select_for_update()` for race-condition-safe booking
- All frontend views use Class-Based Views (CBVs)
- RTL layout with Vazirmatn Persian font
- Frontend booking uses `fetch()` with CSRF token from Django template

## License

No license file is included yet. Add one before open-sourcing or distributing the project.
=======
# HeyMedicApplication-django
This repo made for building and developing a medical platform with name HeyMedic with django and drf
>>>>>>> 71b2fbfcbbba8bfb5f32fd64b9e380d98e443b9d
