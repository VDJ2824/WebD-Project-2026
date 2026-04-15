from django.contrib.auth.models import User

username = "Varima"
password = "Vdj@2824"
email = "admin@example.com"

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username, email, password)
    print("Superuser created")
else:
    print("Superuser already exists")
