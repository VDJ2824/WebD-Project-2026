import os
import json
import firebase_admin
from firebase_admin import credentials, db

# Load Firebase credentials from environment variable
firebase_key = os.environ.get("FIREBASE_KEY")

if not firebase_key:
    raise ValueError("FIREBASE_KEY environment variable not set")

# Convert string → JSON
firebase_config = json.loads(firebase_key)

cred = credentials.Certificate(firebase_config)

# Initialize app
firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ.get(
        'FIREBASE_DATABASE_URL',
        'https://research-paper-webscrapp-e6d2b-default-rtdb.asia-southeast1.firebasedatabase.app/'
    )
})

def get_db():
    return db.reference()
