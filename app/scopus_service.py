import requests
import time
from backend.firebase_config import get_db

API_KEY = "b93eb38460b7dffd67e68bafe5e184cb"


def fetch_papers(author_id):
    url = "https://api.elsevier.com/content/search/scopus"

    params = {
        "query": f"AU-ID({author_id})",
        "httpAccept": "application/json",
        "count": 65,
        "sort": "-coverDate"
    }

    headers = {
        "X-ELS-APIKey": API_KEY
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code != 200:
        return []

    data = response.json()
    return data.get("search-results", {}).get("entry", [])


def store_faculty_and_papers(name, author_id, department, field):
    db = get_db()

    faculty_id = author_id  # use author_id as unique key

    # ✅ store faculty
    db.child("faculties").child(faculty_id).set({
        "name": name,
        "author_id": author_id,
        "department": department,
        "field": field
    })

    papers = fetch_papers(author_id)

    for paper in papers:
        eid = paper.get("eid")

        if not eid:
            continue

        # 🔍 avoid duplicates
        existing = db.child("papers").child(faculty_id)\
            .order_by_child("eid").equal_to(eid).get()

        if existing:
            continue

        paper_data = {
            "title": paper.get("dc:title"),
            "year": int(paper.get("prism:coverDate", "0000")[:4]) if paper.get("prism:coverDate") else 0,
            "scopus_url": f"https://www.scopus.com/record/display.uri?eid={eid}",
            "doi": paper.get("prism:doi"),
            "doi_url": f"https://doi.org/{paper.get('prism:doi')}" if paper.get("prism:doi") else None,
            "faculty_id": faculty_id,
            "citations": int(paper.get("citedby-count", 0)),
            "eid": eid
        }

        db.child("papers").child(faculty_id).push(paper_data)

    # ⏱ sync log
    db.child("sync_logs").child(faculty_id).set({
        "last_sync_time": int(time.time())
    })

    time.sleep(1)  # prevent rate limit
