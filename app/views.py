from django.shortcuts import render, redirect, HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from backend.firebase_config import get_db
from app.scopus_service import store_faculty_and_papers
import time

db = get_db()

def login_view(request):
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username"),
            password=request.POST.get("password")
        )

        if user is not None:
            login(request, user)
            return redirect("dashboard")

        return render(request, "login.html", {
            "error": "Invalid credentials"
        })

    return render(request, "login.html")

from django.contrib.auth.models import User

def signup_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if User.objects.filter(username=username).exists():
            return render(request, "signup.html", {"error": "User already exists"})

        user = User.objects.create_user(
            username=username,
            password=password
        )

        user.is_superuser = False
        user.is_staff = False
        user.save()

        return redirect("login")

    return render(request, "signup.html")

@login_required
def dashboard_view(request):

    faculties = db.child("faculties").get() or {}
    papers = db.child("papers").get() or {}

    total_faculties = len(faculties)
    total_papers = 0
    total_citations = 0

    year_count = {}
    faculty_names = []
    faculty_papers = []
    citations_per_faculty = []
    field_count = {}

    for fid, faculty in faculties.items():
        faculty_name = faculty.get("name", "Unknown Faculty")
        faculty_field = faculty.get("field", "Uncategorized")
        faculty_paper_map = papers.get(fid, {}) or {}

        faculty_names.append(faculty_name)
        faculty_papers.append(len(faculty_paper_map))

        faculty_citations = 0
        for paper in faculty_paper_map.values():
            citations = paper.get("citations", 0)
            try:
                faculty_citations += int(citations)
            except (TypeError, ValueError):
                faculty_citations += 0

            year = paper.get("year", 0)
            if year:
                year_count[year] = year_count.get(year, 0) + 1

            total_papers += 1

        citations_per_faculty.append(faculty_citations)
        total_citations += faculty_citations
        field_count[faculty_field] = field_count.get(faculty_field, 0) + 1

    years = sorted(year_count.keys())
    counts = [year_count[y] for y in years]
    fields = sorted(field_count.keys())
    field_counts = [field_count[field] for field in fields]

    return render(request, "dashboard.html", {
        "username": request.user.username,
        "total_faculties": total_faculties,
        "total_papers": total_papers,
        "total_citations": total_citations,
        "years": years,
        "counts": counts,
        "faculty_names": faculty_names,
        "faculty_papers": faculty_papers,
        "citations_per_faculty": citations_per_faculty,
        "fields": fields,
        "field_counts": field_counts,
    })

@login_required
def faculty_list(request):
    data = db.child("faculties").get() or {}

    faculties = []
    selected_field = request.GET.get('field')
    fields_set = set()

    for fid, f in data.items():
        f['id'] = fid

        if f.get('field'):
            fields_set.add(f['field'])

        if selected_field:
            if f.get('field') == selected_field:
                faculties.append(f)
        else:
            faculties.append(f)

    return render(request, 'faculty.html', {
        'faculties': faculties,
        'fields': sorted(fields_set),
        'field_filter': selected_field,
    })


@login_required
def faculty_profile(request, fid):
    faculty = db.child("faculties").child(fid).get()
    papers = db.child("papers").child(fid).get() or {}

    paper_list = []
    for pid, pdata in papers.items():
        paper_list.append(pdata)

    return render(request, "faculty_profile.html", {
        "faculty": faculty,
        "papers": paper_list
    })


# ADMIN ONLY
@login_required
def add_faculty(request):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=403)

    if request.method == "POST":
        names = request.POST.getlist('name[]')
        ids = request.POST.getlist('author_id[]')
        depts = request.POST.getlist('department[]')
        fields = request.POST.getlist('field[]')

        for i in range(len(names)):
            if names[i].strip():
                store_faculty_and_papers(
                    names[i],
                    ids[i],
                    depts[i],
                    fields[i]
                )

        return redirect('faculty')

    return render(request, 'add_faculty.html')


@login_required
def edit_faculty(request, fid):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=403)

    if request.method == "POST":
        db.child("faculties").child(fid).update({
            "name": request.POST['name'],
            "author_id": request.POST['author_id'],
            "department": request.POST['department'],
            "field": request.POST['field']
        })
        return redirect('faculty')

    faculty = db.child("faculties").child(fid).get()

    return render(request, 'edit_faculty.html', {'faculty': faculty})


@login_required
def delete_faculty(request, fid):
    if not request.user.is_superuser:
        return HttpResponse("Unauthorized", status=403)

    db.child("faculties").child(fid).delete()
    db.child("papers").child(fid).delete()
    return redirect('faculty')

@login_required
def notifications_view(request):
    db = get_db()

    raw = db.child("notifications").get()

    notifications = []
    one_week_ago = int(time.time()) - (7 * 24 * 60 * 60)

    if raw:
        for item in raw.each():
            n = item.val()

            if n.get("timestamp", 0) >= one_week_ago:
                notifications.append(n)

    # sort latest first
    notifications.sort(key=lambda x: x["timestamp"], reverse=True)

    return render(request, "notifications.html", {
        "notifications": notifications
    })

def logout_view(request):
    logout(request)
    return redirect("login")
