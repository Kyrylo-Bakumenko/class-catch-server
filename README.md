# Class Catch Backend

Class Catch Backend is a robust and scalable web service built with Django and PostgreSQL, designed to power the Class Catch application. It provides RESTful APIs for managing classes, implementing custom filtering, and automating data scraping tasks to ensure up-to-date class information.

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the Application](#running-the-application)
- [API Documentation](#api-documentation)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Automated Scraping](#automated-scraping)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Features

- **RESTful APIs:** Built with Django Rest Framework (DRF) to manage class data efficiently.
- **Custom Filtering:** Advanced filtering capabilities to query classes based on various criteria.
- **PostgreSQL Integration:** Reliable and scalable database management for storing class information.
- **Automated Scraping:** A rotating scraper using Proxy-v2 API to collect and update class data periodically.
- **Task Scheduling:** CRON jobs established to automate scraping tasks, ensuring data freshness.
- **Authentication & Authorization:** Secure API endpoints with token-based authentication.
- **Comprehensive Documentation:** Detailed API documentation for easy integration with the frontend.

## Demo

![Class Catch Backend Demo](https://via.placeholder.com/800x400) <!-- Replace with actual demo screenshots -->

Explore the [live demo](https://your-backend-deployment-url.vercel.app) to see the backend APIs in action!

## Getting Started

Follow these instructions to set up the Class Catch Backend locally on your machine for development and testing purposes.

### Prerequisites

Ensure you have the following installed:

- **Python 3.8 or later**
- **pip** (Python package installer)
- **PostgreSQL** (v12 or later)
- **Git**

### Installation

1. **Clone the Repository:**

   ```bash
   git clone https://github.com/yourusername/class-catch-backend.git
   cd class-catch-backend
   ```

2. **Create a Virtual Environment:**

   It's recommended to use a virtual environment to manage dependencies.

   ```bash
   python3 -m venv env
   source env/bin/activate  # On Windows: env\Scripts\activate
   ```

3. **Install Dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

### Configuration

1. **Environment Variables:**

   Create a `.env` file in the root directory and add the following configurations:

   ```env
   DEBUG=True
   SECRET_KEY=your_django_secret_key
   ALLOWED_HOSTS=localhost,127.0.0.1
   DATABASE_NAME=classcatch_db
   DATABASE_USER=your_db_user
   DATABASE_PASSWORD=your_db_password
   DATABASE_HOST=localhost
   DATABASE_PORT=5432
   PROXY_API_KEY=your_proxy_v2_api_key
   ```

   **Note:** Replace the placeholder values with your actual configurations.

2. **Database Setup:**

   Ensure PostgreSQL is running and create a database for the project.

   ```bash
   psql -U your_db_user
   CREATE DATABASE classcatch_db;
   ```

3. **Apply Migrations:**

   ```bash
   python manage.py migrate
   ```

4. **Create a Superuser (Optional):**

   ```bash
   python manage.py createsuperuser
   ```

### Running the Application

Start the development server:

```bash
python manage.py runserver
```

The backend API will be accessible at [http://localhost:8000](http://localhost:8000).

## API Documentation

Class Catch Backend offers a comprehensive set of APIs to interact with class data. You can explore the APIs using tools like [Postman](https://www.postman.com/) or [Swagger](https://swagger.io/).

### Key Endpoints

- **Authentication:**
  - `POST /api/auth/login/` - User login.
  - `POST /api/auth/register/` - User registration.
  - `POST /api/auth/logout/` - User logout.

- **Classes:**
  - `GET /api/classes/` - Retrieve a list of classes with filtering options.
  - `POST /api/classes/` - Create a new class (admin only).
  - `GET /api/classes/{id}/` - Retrieve details of a specific class.
  - `PUT /api/classes/{id}/` - Update a specific class (admin only).
  - `DELETE /api/classes/{id}/` - Delete a specific class (admin only).

### Filtering Parameters

When retrieving classes, you can apply the following filters:

- `department` - Filter by department name.
- `course_level` - Filter by course level (e.g., 100, 200).
- `instructor` - Filter by instructor name.
- `schedule` - Filter by schedule (e.g., Monday 10am).
- `semester` - Filter by semester (e.g., Fall 2025).

**Example Request:**

```http
GET /api/classes/?department=Computer Science&course_level=200&instructor=Dr.%20Smith
```

## Technology Stack

- **Backend Framework:** [Django](https://www.djangoproject.com/) - A high-level Python web framework.
- **API Framework:** [Django Rest Framework (DRF)](https://www.django-rest-framework.org/) - Toolkit for building Web APIs.
- **Database:** [PostgreSQL](https://www.postgresql.org/) - Advanced open-source relational database.
- **Scraping:** [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/) & [Requests](https://docs.python-requests.org/) - Libraries for web scraping.
- **Proxy Management:** [Proxy-v2 API](https://proxyv2api.com/) - For rotating proxies during scraping.
- **Task Scheduling:** [CRON](https://en.wikipedia.org/wiki/Cron) - For automating scraping tasks.
- **Environment Management:** [python-dotenv](https://pypi.org/project/python-dotenv/) - For managing environment variables.

## Project Structure

```
class-catch-backend/
├── classcatch/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── classes/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   ├── filters.py
│   └── tasks.py
├── users/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
├── scraper/
│   ├── __init__.py
│   ├── scraper.py
│   └── proxy_manager.py
├── manage.py
├── requirements.txt
├── .env
├── README.md
└── ...other configuration files
```

## Automated Scraping

To ensure that class data remains current, Class Catch Backend employs an automated scraping system.

### Components

- **Scraper Module (`scraper/scraper.py`):** Contains the logic for scraping class data from external sources.
- **Proxy Manager (`scraper/proxy_manager.py`):** Manages proxy rotations using the Proxy-v2 API to avoid IP blocking.
- **CRON Jobs:** Scheduled tasks that trigger the scraper at predefined intervals.

### Setting Up Automated Scraping

1. **Configure Proxy API:**

   Ensure the `PROXY_API_KEY` is set in your `.env` file.

2. **Define CRON Jobs:**

   Add the following entry to your crontab to run the scraper every day at midnight:

   ```bash
   0 0 * * * /path/to/your/venv/bin/python /path/to/class-catch-backend/manage.py run_scraper
   ```

   **Note:** Replace `/path/to/your/venv/` and `/path/to/class-catch-backend/` with your actual paths.

3. **Create a Custom Management Command:**

   In `classes/management/commands/run_scraper.py`:

   ```python
   from django.core.management.base import BaseCommand
   from classes.tasks import run_scraper_task

   class Command(BaseCommand):
       help = 'Runs the class scraper'

       def handle(self, *args, **kwargs):
           run_scraper_task()
           self.stdout.write(self.style.SUCCESS('Successfully ran the scraper'))
   ```

4. **Implement Scraper Task:**

   In `classes/tasks.py`:

   ```python
   from .scraper import scrape_classes

   def run_scraper_task():
       scrape_classes()
   ```

5. **Scraper Logic:**

   In `scraper/scraper.py`:

   ```python
   import requests
   from bs4 import BeautifulSoup
   from scraper.proxy_manager import get_proxy
   from classes.models import Class
   from django.conf import settings

   def scrape_classes():
       proxy = get_proxy()
       headers = {
           'User-Agent': 'Your User Agent',
       }
       response = requests.get('https://external-class-source.com/classes', headers=headers, proxies=proxy)
       
       if response.status_code == 200:
           soup = BeautifulSoup(response.text, 'html.parser')
           # Parse the HTML to extract class data
           classes = parse_class_data(soup)
           for class_data in classes:
               # Update or create class entries in the database
               Class.objects.update_or_create(
                   class_code=class_data['class_code'],
                   defaults=class_data
               )
       else:
           # Handle failed requests
           pass

   def parse_class_data(soup):
       # Implement parsing logic based on the external source's structure
       return []
   ```

6. **Proxy Management:**

   In `scraper/proxy_manager.py`:

   ```python
   import requests
   from django.conf import settings

   def get_proxy():
       proxy_api_url = 'https://proxyv2api.com/get'
       params = {
           'api_key': settings.PROXY_API_KEY,
           'type': 'http',
           'country': 'us',
       }
       response = requests.get(proxy_api_url, params=params)
       if response.status_code == 200:
           proxy_data = response.json()
           return {
               'http': f"http://{proxy_data['proxy']}",
               'https': f"https://{proxy_data['proxy']}",
           }
       else:
           return None
   ```

### Monitoring and Logs

Ensure that you monitor the scraping tasks by checking logs or implementing alerting mechanisms to handle failures or anomalies in the scraping process.

## Contributing

We welcome contributions to Class Catch Backend! To get started:

1. **Fork the Repository**

2. **Create a Feature Branch:**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Commit Your Changes:**

   ```bash
   git commit -m "Add some feature"
   ```

4. **Push to the Branch:**

   ```bash
   git push origin feature/YourFeature
   ```

5. **Open a Pull Request**

Please ensure your code follows the project's coding standards and includes relevant tests.

## License

This project is licensed under the [MIT License](LICENSE). See the [LICENSE](LICENSE) file for details.

## Contact

For any inquiries or feedback, please reach out to:

- **Email:** kyrylo.bakumenko@gmail.com
- **GitHub:** [@kyrylo-bakumenko](https://github.com/kyrylo-bakumenko)
- **LinkedIn:** [Kyrylo Bakumenko](https://www.linkedin.com/in/kyrylo-bakumenko)
