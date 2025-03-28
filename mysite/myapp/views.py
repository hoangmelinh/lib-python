from django.shortcuts import render
from .models import Book

def home(request):
    return render(request, 'home.html')

def search_page(request):
    query = request.GET.get("query", "")
    return render(request, "search.html", {"query": query})

def book_list(request):
    books = Book.objects.all()
    return render(request, 'book.html', {'books': books})

from django.shortcuts import render

def login_view(request):
    return render(request, 'login.html')
