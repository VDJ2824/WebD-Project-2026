import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from scopus_service import update_all_faculty_data

if __name__ == "__main__":
    update_all_faculty_data()
