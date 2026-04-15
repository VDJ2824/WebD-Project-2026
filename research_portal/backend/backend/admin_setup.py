from firebase_config import get_db

db = get_db()

db.child("admins").push({
    "username": "Varima",
    "password": "Vdj@2824"
})