<<<<<<< HEAD
# HeyMedic

HeyMedic is a Django-based healthcare platform for connecting patients and doctors. It supports phone-number authentication, role-based access (admin, patient, doctor), and is structured to grow into appointment booking, payments, and reviews.

The project is in early development: the core user system and website are in place, with additional apps scaffolded for upcoming features.

## Features

### Implemented

- **Custom user model** — Phone number as the primary login identifier (Iran region default via `django-phonenumber-field`)
- **Role-based users** — Admin, Patient, and Doctor roles with an `is_verified` flag
- **Django Admin** — Customized user management in the admin panel
- **Website** — Basic landing page at `/`
- **REST API foundation** — Django REST Framework, JWT, Djoser, and OpenAPI docs (drf-spectacular) included in dependencies
- **Docker support** — PostgreSQL and Django backend via Docker Compose

### Planned (scaffolded apps)

| App            | Purpose                          |
|----------------|----------------------------------|
| `appointments` | Doctor–patient appointment scheduling |
| `payments`     | Payment processing               |
| `reviews`      | Patient reviews and ratings      |

These apps exist in the codebase but are not yet registered in `INSTALLED_APPS` or wired to URLs.

## Tech Stack

| Layer        | Technology |
|--------------|------------|
| Backend      | Django 6.0, Python 3.12 |
| API          | Django REST Framework, Simple JWT, Djoser, drf-spectacular |
| Database     | PostgreSQL (production/Docker) or SQLite (local dev) |
| Auth         | Custom user model, phone-number login |
| Async tasks  | Celery, Redis, django-celery-results (dependencies included) |
| Deployment   | Gunicorn, Docker |
| Dev tools    | pytest, pytest-django, black, flake8, Faker |

## Project Structure

```
HeyMdicApplication/
├── core/                      # Django project root
│   ├── core/                  # Project settings, URLs, WSGI/ASGI
│   ├── accounts/              # Custom User model and admin
│   ├── website/               # Public-facing pages
│   ├── appointments/          # (planned) Appointment scheduling
│   ├── payments/              # (planned) Payment handling
│   ├── reviews/               # (planned) Reviews and ratings
│   └── manage.py
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## Prerequisites

- Python 3.12+
- pip
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/) (optional, for containerized setup)
- PostgreSQL 17 (optional; SQLite works for local development)

## Environment Variables

Create a `.env` file in the project root. Example:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database — use sqlite3 for simple local dev
DATABASE_ENGINE=sqlite3
DATABASE_NAME=db.sqlite3

# Database — use postgresql with Docker or a local Postgres instance
# DATABASE_ENGINE=postgresql
# DATABASE_NAME=heymedic
# DATABASE_USERNAME=heymedic
# DATABASE_PASSWORD=your-password
# DATABASE_HOST=db
# DATABASE_PORT=5432
```

| Variable               | Description                                      | Default              |
|------------------------|--------------------------------------------------|----------------------|
| `DJANGO_SECRET_KEY`    | Django secret key                                | `fallback-secret-key` |
| `DEBUG`                | Enable debug mode                                | `True`               |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts                    | `backend`            |
| `DATABASE_ENGINE`      | `sqlite3` or `postgresql`                        | —                    |
| `DATABASE_NAME`        | Database name or SQLite file path                | `db.sqlite3`         |
| `DATABASE_USERNAME`    | PostgreSQL username                              | —                    |
| `DATABASE_PASSWORD`    | PostgreSQL password                              | —                    |
| `DATABASE_HOST`        | PostgreSQL host                                  | `localhost`          |
| `DATABASE_PORT`        | PostgreSQL port                                  | `5432`               |

## Getting Started

### Option 1: Local development (virtual environment)

```bash
# Clone the repository
git clone <repository-url>
cd HeyMdicApplication

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create a .env file in the project root (see Environment Variables above)

# Run migrations
cd core
python manage.py migrate

# Create a superuser (uses phone number as username)
python manage.py createsuperuser

# Start the development server
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) for the home page and [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) for the admin panel.

### Option 2: Docker Compose

```bash
# Create .env with PostgreSQL settings (see Environment Variables)
# DATABASE_ENGINE=postgresql
# DATABASE_HOST=db

docker compose up --build
```

The backend runs at [http://localhost:8000/](http://localhost:8000/). PostgreSQL is exposed on port `5432`.

Run migrations inside the container:

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
```

## User Model

The custom `accounts.User` model extends Django's `AbstractUser` with:

| Field          | Description                                      |
|----------------|--------------------------------------------------|
| `phone_number` | Unique identifier used for login (`USERNAME_FIELD`) |
| `email`        | Optional, unique email address                   |
| `role`         | `admin`, `patient`, or `doctor`                  |
| `is_verified`  | Whether the account has been verified            |
| `created_at`   | Account creation timestamp                       |

Superusers are created with `role=admin` and `is_verified=True` via the custom `UserManager`.

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

- Static files: `core/static/` → collected to `core/staticfiles/`
- Media uploads: `core/media/`

```bash
python manage.py collectstatic
```

## API (planned)

Dependencies for a REST API are installed (`djangorestframework`, `djangorestframework-simplejwt`, `djoser`, `drf-spectacular`), and `REST_FRAMEWORK` is configured with OpenAPI schema support. API endpoints and URL routing are not yet implemented.

## Roadmap

- [ ] Register and implement `appointments`, `payments`, and `reviews` apps
- [ ] REST API endpoints with JWT authentication
- [ ] OpenAPI/Swagger documentation UI
- [ ] Celery task queue configuration
- [ ] Email verification and notifications
- [ ] Production deployment with Gunicorn

## License

No license file is included yet. Add one before open-sourcing or distributing the project.
=======
# HeyMedicApplication-django
This repo made for building and developing a medical platform with name HeyMedic with django and drf
>>>>>>> 71b2fbfcbbba8bfb5f32fd64b9e380d98e443b9d
