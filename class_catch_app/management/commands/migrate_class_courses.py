# class_catch_app/management/commands/migrate_class_to_course.py

from django.core.management.base import BaseCommand
from class_catch_app.models import Class, Course

class Command(BaseCommand):
    help = 'Migrates legacy Class data into the new Course model.'

    def handle(self, *args, **options):
        self.stdout.write("Starting migration from Class to Course...")
        migrated_count = 0
        skipped_count = 0

        # Iterate over every legacy Class instance
        for legacy in Class.objects.all():
            # Compute a composite key; adjust the logic as needed.
            course_id = f"{legacy.class_code}.{legacy.course_number}-{legacy.term}"
            
            # Build the mapping for the new Course record.
            defaults = {
                'subject_id': legacy.class_code,
                'course_number': legacy.course_number,
                'name': legacy.title,
                # Set new API fields to None or default values
                'is_active': True,
                'orc_title': None,
                'orc_description': None,
                'distributives': None,
                'culture_options': None,
                'schools': None,
                # 'last_updated' will be auto-set.
            }
            
            # Create or update the Course record.
            # If a Course with this course_id already exists, update its fields.
            course_obj, created = Course.objects.update_or_create(
                course_id=course_id,
                defaults=defaults
            )
            if created:
                migrated_count += 1
                self.stdout.write(f"Created Course: {course_id}")
            else:
                migrated_count += 1
                self.stdout.write(f"Updated Course: {course_id}")
                
        self.stdout.write(self.style.SUCCESS(
            f"Migration complete: {migrated_count} records migrated (skipped {skipped_count})."
        ))
