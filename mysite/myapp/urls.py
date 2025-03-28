from django.contrib import admin
from django.urls import path
from .views import home, search_page
from myapp import views  # 🔥 Thêm dòng này để import views
from .views import book_list
from .views import login_view 

urlpatterns = [
    path('', home, name='home'),
    path('search/', search_page, name='search'),
    path('book/', book_list, name='book'),
    path('admin/', admin.site.urls),
    path('login/', login_view, name='login'),
] 
