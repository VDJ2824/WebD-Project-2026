from django.urls import path
from . import views

urlpatterns = [
    path('', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    path('faculty/', views.faculty_list, name='faculty'),
    path('faculty/add/', views.add_faculty, name='add_faculty'),
    path('faculty/edit/<str:fid>/', views.edit_faculty, name='edit_faculty'),
    path('faculty/delete/<str:fid>/', views.delete_faculty, name='delete_faculty'),
    path('faculty/<str:fid>/', views.faculty_profile, name='faculty_profile'),

    path('notifications/', views.notifications_view, name='notifications'),
    path('logout/', views.logout_view, name='logout'),
]
