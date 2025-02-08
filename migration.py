# In a new migration file
from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('class_catch_app', 'previous_migration_name'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Class',
            new_name='Course',
        ),
    ]
