from django.shortcuts import render, get_object_or_404, redirect
from .models import Book, Giaotrinh
from django.contrib.auth.forms import UserCreationForm
from myapp.models import CreateRegister
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q 
from django.contrib.auth.decorators import login_required
from .recommend import recommend_books
from .models import Book, UserHistory
import pandas as pd


def register_view(request):
    form = CreateRegister()
    if request.method == "POST":
        form = CreateRegister(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect("login")  # Chuyển hướng đến trang đăng nhập
        else:
            messages.error(request, "Đăng ký thất bại. Vui lòng kiểm tra lại thông tin.")

    context = {'form': form}
    return render(request, 'register.html', context)

from django.db.models import Case, When

def home(request):
    user = request.user
    books = Book.objects.all()
    recommended = []

    if user.is_authenticated:
        history = UserHistory.objects.filter(user=user).values_list('book_id', flat=True)
        books_df = pd.DataFrame(list(books.values('id', 'title', 'author')))
        books_df['combined'] = books_df['title'] + ' ' + books_df['author']

        history_dict = {user.id: list(history)}
        recommended_df = recommend_books(user.id, books_df, history_dict)

        # Lấy danh sách Book theo thứ tự ID trong recommended
        recommended_ids = list(recommended_df['id'])
        preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(recommended_ids)])
        recommended = list(Book.objects.filter(id__in=recommended_ids).order_by(preserved_order))

    return render(request, 'home.html', {
        'books': books,
        'recommended_books': recommended
    })


def intro_ptit(request):
    return render(request, 'intro.html')

@login_required(login_url='/login/')
def search_page(request):
    query = request.GET.get('q', '')
    category = request.GET.get('category', 'all')  # Mặc định là "all"

    books = []
    giaotrinhs = []

    if query:
        if category == 'book':
            books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
        elif category == 'giaotrinh':
            giaotrinhs = Giaotrinh.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
        elif category == 'all':  # Tìm cả sách và giáo trình
            books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
            giaotrinhs = Giaotrinh.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))

    return render(request, 'search.html', {
        'query': query,
        'category': category,
        'books': books,
        'giaotrinhs': giaotrinhs
    })


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

def search_page1(request):
    query = request.GET.get('q', '')
    if query:
        giaotrinhs = Giaotrinh.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
        if giaotrinhs.count() == 1:
            return redirect('book_detail', book_id=books.first().id)
        return render(request, 'search_gtrinh.html', {'giaotrinhs': giaotrinhs, 'query': query})
    return redirect('home')

def recommended_books(request):
    user = request.user
    books = Book.objects.all()
    history = UserHistory.objects.filter(user=user).values_list('book_id', flat=True)

    books_df = pd.DataFrame(list(books.values('id', 'title', 'description')))
    history_dict = {user.id: list(history)}

    recommendations = recommend_books(user.id, books_df, history_dict)
    return render(request, 'home.html', {'home': home})

def giaotrinh_detail(request, giaotrinh_id):
    giaotrinh = get_object_or_404(Giaotrinh, id=giaotrinh_id)
    return render(request, 'giaotrinh_detail.html', {'giaotrinh': giaotrinh})
