from django.contrib import admin
from django.urls import path
from .import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_page, name='search'),
    path('book/', views.book_list, name='book'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
     path('book/<int:book_id>/', views.book_detail, name='book_detail'),
] 
