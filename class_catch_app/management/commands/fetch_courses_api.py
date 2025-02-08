# class_catch_app/management/commands/fetch_courses_api.py
import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from class_catch_app.models import Course

class Command(BaseCommand):
    help = 'Fetches course data from the Dartmouth Academic API and updates the database.'

    def get_jwt_token(self, scopes):
        """
        Call the DartAPI login service to retrieve a JWT token.
        """
        jwt_url = f"{settings.DART_API_BASE_URL}/jwt"
        headers = {
            "Authorization": settings.DART_API_KEY,
        }
        # Construct the scope parameter as a space-separated list
        params = {}
        if scopes:
            params["scope"] = " ".join(scopes)
        
        self.stdout.write("Requesting JWT token...")
        response = requests.post(jwt_url, headers=headers, params=params, timeout=30)
        if response.status_code != 200:
            raise Exception(f"JWT token request failed: {response.status_code} {response.text}")
        data = response.json()
        accepted_scopes = data.get('accepted_scopes', [])
        self.stdout.write(f"JWT acquired with scopes: {accepted_scopes}")
        return data.get("jwt")

    def fetch_courses(self, jwt_token):
        """
        Fetch all courses from the Academic Courses API.
        """
        api_url = f"{settings.DART_API_BASE_URL}/academic/courses"
        headers = {
            "Authorization": f"Bearer {jwt_token}"
        }
        self.stdout.write("Fetching courses data from the API...")
        response = requests.get(api_url, headers=headers, timeout=30)
        if response.status_code != 200:
            raise Exception(f"Failed to fetch courses: {response.status_code} {response.text}")
        
        # The API should return a JSON list of courses.
        courses_data = response.json()
        return courses_data

    def update_database(self, courses_data):
        """
        Create or update Course objects based on the API response.
        """
        self.stdout.write("Processing courses data...")
        new_count = 0
        update_count = 0

        for course in courses_data:
            # Use the API's composite ID (e.g. "AAAS.023-201503") as our unique key
            course_id = course.get("id")
            if not course_id:
                continue  # Skip any unexpected record

            defaults = {
                "subject_id": course.get("subject_id"),
                "course_number": course.get("course_number"),
                "name": course.get("name"),
                "is_active": course.get("is_active", True),
                "orc_title": course.get("orc_title"),
                "orc_description": course.get("orc_description"),
                "distributives": course.get("distributives"),
                "culture_options": course.get("culture_options"),
                "schools": course.get("schools"),
            }

            obj, created = Course.objects.update_or_create(
                course_id=course_id,
                defaults=defaults
            )
            if created:
                new_count += 1
                self.stdout.write(self.style.SUCCESS(f"Created course {course_id}"))
            else:
                update_count += 1
                self.stdout.write(self.style.SUCCESS(f"Updated course {course_id}"))

        self.stdout.write(self.style.SUCCESS(f"Courses processing complete: {new_count} new, {update_count} updated."))

    def handle(self, *args, **options):
        start_time = time.time()
        try:
            # Step 1: Authenticate to get a JWT token.
            jwt_token = self.get_jwt_token(settings.DART_API_SCOPES)
            # Step 2: Fetch courses data.
            courses_data = self.fetch_courses(jwt_token)
            # Step 3: Process and update the database.
            self.update_database(courses_data)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
            return

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"API data fetch completed in {elapsed:.2f} seconds"))
