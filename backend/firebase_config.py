import os
import json
import firebase_admin
from firebase_admin import credentials, db

firebase_json = os.getenv("FIREBASE_SERVICE_ACCOUNT")
db_url = os.getenv("FIREBASE_DATABASE_URL")

if not firebase_json:
    raise ValueError("Missing FIREBASE_SERVICE_ACCOUNT")

firebase_config = json.loads(firebase_json)

# 🔥 CRITICAL FIX FOR JWT ERROR
firebase_config["private_key"] = firebase_config["private_key"].replace("\\n", "\n")

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred, {
        "databaseURL": db_url
    })


def get_db():
    return db.reference()
    
