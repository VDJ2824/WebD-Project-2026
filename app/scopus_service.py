import requests
import time
import os 
from backend.firebase_config import get_db

API_KEY = os.getenv("SCOPUS_API_KEY", "ff63bce5bcb9772f8a90f10f5e7ab5c4")

def fetch_papers(author_id):
    url = "https://api.elsevier.com/content/search/scopus"

    headers = {
        "X-ELS-APIKey": API_KEY
    }

    start = 0
    count = 25
    all_papers = []
    last_status_code = 200

    while True:
        params = {
            "query": f"AU-ID({author_id})",
            "httpAccept": "application/json",
            "count": count,
            "start": start,
            "sort": "-coverDate"
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

        last_status_code = response.status_code

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

        if not papers:
            break

        all_papers.extend(papers)

        if len(papers) < count:
            break

        start += count

    return {
        "ok": True,
        "status_code": last_status_code,
        "papers": all_papers,
        "error": "",
    }


def calculate_h_index(citations):
    valid_citations = sorted(
        [max(0, int(citation)) for citation in citations if citation is not None],
        reverse=True
    )

    h_index = 0
    for index, citation_count in enumerate(valid_citations, start=1):
        if citation_count >= index:
            h_index = index
        else:
            break

    return h_index


def compute_metrics_from_papers(papers):
    citations_list = []

    for paper in papers:
        if not isinstance(paper, dict):
            continue

        citation_value = paper.get("citedby-count", paper.get("citations", 0))
        try:
            citations_list.append(int(citation_value))
        except (TypeError, ValueError):
            citations_list.append(0)

    total_citations = sum(citations_list)
    document_count = len(citations_list)

    citations_list.sort(reverse=True)

    h_index = 0
    for i, citation_count in enumerate(citations_list, start=1):
        if citation_count >= i:
            h_index = i
        else:
            break

    return {
        "h_index": h_index,
        "citations": total_citations,
        "documents": document_count,
    }


def values_differ(old_value, new_value):
    return old_value != new_value


def get_metrics_changes(old_metrics, new_metrics):
    tracked_fields = ("h_index", "citations", "documents")
    changes = {}

    old_metrics = old_metrics if isinstance(old_metrics, dict) else {}

    for field in tracked_fields:
        old_value = old_metrics.get(field, 0)
        new_value = new_metrics.get(field, 0)
        if values_differ(old_value, new_value):
            changes[field] = {
                "old": old_value,
                "new": new_value,
            }

    return changes


def get_paper_changes(old_data, new_data):
    tracked_fields = (
        "title",
        "year",
        "scopus_url",
        "doi",
        "doi_url",
        "citations",
    )
    changes = {}

    old_data = old_data if isinstance(old_data, dict) else {}

    for field in tracked_fields:
        old_value = old_data.get(field)
        new_value = new_data.get(field)
        if values_differ(old_value, new_value):
            changes[field] = {
                "old": old_value,
                "new": new_value,
            }

    return changes


def fetch_and_store_author_metrics(author_id):
    db = get_db()
    timestamp = int(time.time())
    old_metrics = db.child("faculties").child(author_id).child("metrics").get() or {}
    metrics = {
        "h_index": None,
        "citations": None,
        "documents": None,
        "last_updated": timestamp,
    }

    url = f"https://api.elsevier.com/content/author/author_id/{author_id}"
    headers = {
        "X-ELS-APIKey": API_KEY
    }
    params = {
        "view": "METRICS",
        "httpAccept": "application/json",
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=20)

        if response.status_code == 200:
            data = response.json()
            author_data = data.get("author-retrieval-response", [])
            if author_data:
                author_profile = author_data[0]
                h_index = author_profile.get("h-index")
                coredata = author_profile.get("coredata", {}) or {}
                citation_count = coredata.get("citation-count")
                document_count = coredata.get("document-count")

                if h_index not in (None, ""):
                    metrics["h_index"] = int(h_index)
                if citation_count not in (None, ""):
                    metrics["citations"] = int(citation_count)
                if document_count not in (None, ""):
                    metrics["documents"] = int(document_count)
    except (requests.RequestException, ValueError, TypeError):
        pass

    try:
        papers = db.child("papers").child(author_id).get() or {}
        paper_list = list(papers.values()) if isinstance(papers, dict) else []
        computed_metrics = compute_metrics_from_papers(paper_list)

        if metrics["h_index"] is None:
            metrics["h_index"] = computed_metrics["h_index"]
        if metrics["citations"] is None:
            metrics["citations"] = computed_metrics["citations"]
        if metrics["documents"] is None:
            metrics["documents"] = computed_metrics["documents"]
    except Exception:
        pass

    metrics["h_index"] = 0 if metrics["h_index"] is None else metrics["h_index"]
    metrics["citations"] = 0 if metrics["citations"] is None else metrics["citations"]
    metrics["documents"] = 0 if metrics["documents"] is None else metrics["documents"]

    try:
        db.child("faculties").child(author_id).update({
            "metrics": metrics
        })
    except Exception:
        pass

    return {
        "metrics": metrics,
        "changes": get_metrics_changes(old_metrics, metrics),
    }


def store_faculty_and_papers(name, author_id, department, field, salutation=""):
    db = get_db()

    faculty_id = author_id

    db.child("faculties").child(faculty_id).set({
        "salutation": salutation,
        "name": name,
        "author_id": author_id,
        "department": department,
        "field": field
    })

    fetch_result = fetch_papers(author_id)
    papers = fetch_result["papers"]

    stored_count = 0
    skipped_count = 0

    new_papers = 0
    updated_papers = 0
    updated_fields = set()
    paper_change_details = []

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
                "last_updated": int(time.time()) 
            }

            existing = db.child("papers").child(faculty_id)\
                .order_by_child("eid").equal_to(eid).get()

            if existing:
                for item_key, old_data in existing.items():
                    changes = get_paper_changes(old_data, paper_data)
                    if changes:
                        db.child("papers").child(faculty_id).child(item_key).update(paper_data)
                        updated_papers += 1
                        updated_fields.update(changes.keys())
                        paper_change_details.append({
                            "eid": eid,
                            "title": paper_data["title"],
                            "changed_fields": sorted(changes.keys()),
                        })
                    else:
                        skipped_count += 1
            else:
                db.child("papers").child(faculty_id).push(paper_data)
                stored_count += 1
                new_papers += 1

    metrics_result = fetch_and_store_author_metrics(author_id)
    metrics = metrics_result["metrics"]
    metrics_changes = metrics_result["changes"]

    if new_papers > 0 or updated_papers > 0 or metrics_changes:
        db.child("notifications").push({
            "faculty_id": faculty_id,
            "faculty_name": name,
            "new_papers": new_papers,
            "updated_papers": updated_papers,
            "metrics_changed": bool(metrics_changes),
            "metrics_changes": metrics_changes,
            "updated_fields": sorted(updated_fields),
            "paper_change_details": paper_change_details,
            "documents": metrics.get("documents", 0),
            "citations": metrics.get("citations", 0),
            "h_index": metrics.get("h_index", 0),
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
        "updated_papers": updated_papers, 
        "new_papers": new_papers,         
        "metrics_changed": bool(metrics_changes),
        "metrics_changes": metrics_changes,
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

    faculty_items = faculties.values() if isinstance(faculties, dict) else []

    for data in faculty_items:
        if not isinstance(data, dict):
            continue

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
