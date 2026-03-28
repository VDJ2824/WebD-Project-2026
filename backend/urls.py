from django.urls import path
from django.contrib import admin   # ✅ ADD THIS
from app import views

urlpatterns = [
    # 🔐 Django Admin Panel
    path('admin/', admin.site.urls),   # ✅ ADD THIS

    # 🔐 Auth
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),

    # 🏠 Main App
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # 👨‍🏫 Faculty
    path('faculty/', views.faculty_list, name='faculty'),
    path('faculty/add/', views.add_faculty, name='add_faculty'),
    path('faculty/<str:fid>/', views.faculty_profile, name='faculty_profile'),
    
    path('faculty/edit/<str:fid>/', views.edit_faculty, name='edit_faculty'),
    path('faculty/delete/<str:fid>/', views.delete_faculty, name='delete_faculty'),
]