import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from scopus_service import update_all_faculty_data

if __name__ == "__main__":
    update_all_faculty_data()
