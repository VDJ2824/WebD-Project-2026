import os
import json
import firebase_admin
from firebase_admin import credentials, db

firebase_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

if not firebase_json:
    raise ValueError("FIREBASE_SERVICE_ACCOUNT not set")

firebase_config = json.loads(firebase_json)

if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)

    firebase_admin.initialize_app(cred, {
        'databaseURL': os.environ.get('FIREBASE_DATABASE_URL')
    })


def get_db():
    return db.reference()
