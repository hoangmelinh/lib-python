from django.shortcuts import render, get_object_or_404, redirect
from .models import Book
from django.contrib.auth.forms import UserCreationForm
from myapp.models import CreateRegister
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q 

def register_view(request):
    form = CreateRegister()
    if request.method == "POST" :
        form = CreateRegister(request.POST)
        if form.is_valid :
            form.save()
    context = {'form' : form}
    return render(request, 'register.html', context)

def home(request):
    return render(request, 'home.html')

def search_page(request):
    query = request.GET.get('q', '')
    if query:
        books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
        if books.count() == 1:
            return redirect('book_detail', book_id=books.first().id)
        return render(request, 'search.html', {'books': books, 'query': query})
    return redirect('home')



def book_list(request):
    books = Book.objects.all()
    return render(request, 'book.html', {'books': books})

from django.shortcuts import render

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            # Thêm remember me functionality
            if request.POST.get('remember_me'):
                request.session.set_expiry(30 * 24 * 60 * 60)  # 30 ngày
            else:
                request.session.set_expiry(0)  # Khi trình duyệt đóng
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password!')
        if user is None:
             print("Authentication failed")

    
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'book.html', {'book': book})