import os
import firebase_admin
from firebase_admin import credentials, db

# Short list of paths for service account key (file exists in backend/backend/)
CANDIDATE_KEYS = [
    os.environ.get('FIREBASE_SERVICE_ACCOUNT'),
    os.path.join(os.path.dirname(__file__), 'serviceAccountKey.json'),
    os.path.join(os.path.dirname(__file__), '..', 'scripts', 'serviceAccountKey.json'),
]

service_account_file = next(
    (os.path.abspath(p) for p in CANDIDATE_KEYS if p and os.path.isfile(os.path.abspath(p))),
    None,
)
if service_account_file is None:
    raise FileNotFoundError(
        'Firebase service account key not found. Place serviceAccountKey.json in backend/backend or scripts, '
        'or set FIREBASE_SERVICE_ACCOUNT environment variable.'
    )

cred = credentials.Certificate(service_account_file)

firebase_admin.initialize_app(cred, {
    'databaseURL': os.environ.get('FIREBASE_DATABASE_URL', 'https://research-paper-webscrapp-e6d2b-default-rtdb.asia-southeast1.firebasedatabase.app/')
})

def get_db():
    return db.reference()