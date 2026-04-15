import requests
import time
import os  # 🔥 ADDED
from backend.firebase_config import get_db

# 🔥 ADDED (safe fallback)
API_KEY = os.getenv("SCOPUS_API_KEY", "ff63bce5bcb9772f8a90f10f5e7ab5c4")


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

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)
    except requests.RequestException as exc:
        return {
            "ok": False,
            "status_code": None,
            "papers": [],
            "error": f"Request failed: {exc}",
        }

    if response.status_code != 200:
        return {
            "ok": False,
            "status_code": response.status_code,
            "papers": [],
            "error": response.text[:300] or "Scopus API returned a non-200 response.",
        }

    try:
        data = response.json()
    except ValueError:
        return {
            "ok": False,
            "status_code": response.status_code,
            "papers": [],
            "error": "Scopus API returned invalid JSON.",
        }

    papers = data.get("search-results", {}).get("entry", [])
    return {
        "ok": True,
        "status_code": response.status_code,
        "papers": papers,
        "error": "",
    }


def store_faculty_and_papers(name, author_id, department, field):
    db = get_db()

    faculty_id = author_id

    db.child("faculties").child(faculty_id).set({
        "name": name,
        "author_id": author_id,
        "department": department,
        "field": field
    })

    fetch_result = fetch_papers(author_id)
    papers = fetch_result["papers"]

    stored_count = 0
    skipped_count = 0

    # 🔥 ADDED (tracking updates)
    new_papers = 0
    updated_papers = 0

    if fetch_result["ok"]:
        for paper in papers:
            eid = paper.get("eid")

            if not eid:
                skipped_count += 1
                continue

            paper_data = {
                "title": paper.get("dc:title"),
                "year": int(paper.get("prism:coverDate", "0000")[:4]) if paper.get("prism:coverDate") else 0,
                "scopus_url": f"https://www.scopus.com/record/display.uri?eid={eid}",
                "doi": paper.get("prism:doi"),
                "doi_url": f"https://doi.org/{paper.get('prism:doi')}" if paper.get("prism:doi") else None,
                "faculty_id": faculty_id,
                "citations": int(paper.get("citedby-count", 0)),
                "eid": eid,
                "last_updated": int(time.time())  # 🔥 ADDED
            }

            existing = db.child("papers").child(faculty_id)\
                .order_by_child("eid").equal_to(eid).get()

            # 🔥 UPDATED LOGIC (UPSERT)
            if existing.each():
                for item in existing.each():
                    old_data = item.val()

                    # 🔄 detect change
                    if old_data.get("citations") != paper_data["citations"] or \
                       old_data.get("title") != paper_data["title"] or \
                       old_data.get("doi") != paper_data["doi"]:

                        db.child("papers").child(faculty_id).child(item.key()).update(paper_data)
                        updated_papers += 1
                    else:
                        skipped_count += 1
            else:
                db.child("papers").child(faculty_id).push(paper_data)
                stored_count += 1
                new_papers += 1

    # 🔔 ADDED: notifications
    if new_papers > 0 or updated_papers > 0:
        db.child("notifications").push({
            "faculty_id": faculty_id,
            "faculty_name": name,
            "new_papers": new_papers,
            "updated_papers": updated_papers,
            "timestamp": int(time.time())
        })

    # ⏱ sync log (UNCHANGED)
    db.child("sync_logs").child(faculty_id).set({
        "last_sync_time": int(time.time()),
        "status": "success" if fetch_result["ok"] else "error",
        "fetched_count": len(papers),
        "stored_count": stored_count,
        "skipped_count": skipped_count,
        "error": fetch_result["error"],
        "status_code": fetch_result["status_code"],
    })

    time.sleep(1)

    return {
        "status": "success" if fetch_result["ok"] else "error",
        "fetched_count": len(papers),
        "stored_count": stored_count,
        "skipped_count": skipped_count,
        "updated_papers": updated_papers,  # 🔥 ADDED
        "new_papers": new_papers,          # 🔥 ADDED
        "error": fetch_result["error"],
        "status_code": fetch_result["status_code"],
    }


def update_all_faculty_data():
    db = get_db()

    faculties = db.child("faculties").get()

    if not faculties:
        print("No faculties found.")
        return

    total = 0

    for faculty in faculties.each():
        data = faculty.val()

        name = data.get("name")
        author_id = data.get("author_id")
        department = data.get("department")
        field = data.get("field")

        print(f"\n🔄 Updating: {name}")

        result = store_faculty_and_papers(
            name,
            author_id,
            department,
            field
        )

        print(f"✔ Done: {result}")
        total += 1

    print(f"\n✅ Completed updating {total} faculties")