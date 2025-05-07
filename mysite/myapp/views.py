import os, re, uuid, logging, pytesseract
import pandas as pd

from PIL import Image, ImageEnhance, ImageFilter
from urllib.parse import urljoin
from rapidfuzz import process

from django.conf import settings
from django.utils import timezone
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from django.db.models import Q, Case, When
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

from .models import Book, Giaotrinh, UserHistory, BorrowRecord
from .forms import BookCoverForm, UserUpdateForm
from .recommend import recommend_books
from myapp.models import CreateRegister



pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'

logger = logging.getLogger(__name__)



def register_view(request):
    form = CreateRegister()
    if request.method == "POST":
        form = CreateRegister(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Đăng ký thành công! Vui lòng đăng nhập.")
            return redirect("login")  

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
    user = request.user
    query = request.GET.get('q', '')
    category = request.GET.get('category', 'all')

    books = []
    giaotrinhs = []
    recommended_books = []

    if query:
        if category == 'book':
            books = Book.objects.filter(Q(title__icontains=query))
        elif category == 'giaotrinh':
            giaotrinhs = Giaotrinh.objects.filter(Q(title__icontains=query))
        elif category == 'all':
            books = Book.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))
            giaotrinhs = Giaotrinh.objects.filter(Q(title__icontains=query) | Q(author__icontains=query))

    # Recommend nên xử lý riêng nếu user đã login
    if user.is_authenticated:
        history = UserHistory.objects.filter(user=user).values_list('book_id', flat=True)
        books_df = pd.DataFrame(list(Book.objects.values('id', 'title', 'author')))
        books_df['combined'] = books_df['title'] + ' ' + books_df['author']

        history_dict = {user.id: list(history)}
        recommended_df = recommend_books(user.id, books_df, history_dict)

        if not recommended_df.empty:
            recommended_ids = list(recommended_df['id'])
            preserved_order = Case(*[When(id=pk, then=pos) for pos, pk in enumerate(recommended_ids)])
            recommended_books = list(Book.objects.filter(id__in=recommended_ids).order_by(preserved_order))

    return render(request, 'search.html', {
        'query': query,
        'category': category,
        'books': books,
        'giaotrinhs': giaotrinhs,
        'recommended_books': recommended_books
    })


def book_list(request):
    books = Book.objects.all()
    return render(request, 'book.html', {'books': books})


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



@login_required
def profile_view(request):
    user = request.user
    borrowed_books = BorrowRecord.objects.filter(user=user)
    returned_books = borrowed_books.exclude(returned_at=None)
    viewed_books = UserHistory.objects.filter(user=user).select_related('book').order_by('-viewed_at')

    return render(request, 'user/profile.html', {
        'user': user,
        'borrowed_books': borrowed_books,
        'returned_books': returned_books,
        'viewed_books': viewed_books,
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Cập nhật thông tin thành công.")
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)

    return render(request, 'user/edit_profile.html', {'form': form})

def book_detail(request, book_id):
    book = get_object_or_404(Book, id=book_id)
    return render(request, 'book.html', {'book': book})


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


def preprocess_image(image):

    try:

        image = image.convert('L')


        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.8)

        image = ImageEnhance.Sharpness(image).enhance(1.5)


        return image
    except Exception as e:
        logger.error(f"Lỗi tiền xử lý ảnh: {str(e)}")
        raise



def optimize_ocr_for_vietnamese(image):
    """Optimized OCR configuration for mixed English/Vietnamese text"""
    try:
        config = r'''
        -l eng+vie
        --oem 3
        --psm 6  
        --dpi 300
        -c preserve_interword_spaces=1
        -c tessedit_char_blacklist=|\\`~_@
        -c textord_space_size_is_variable=1
        '''
        text = pytesseract.image_to_string(image, config=config)
        logger.info(f"OCR Raw Output: {text}")
        
      
        text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  
        text = re.sub(r'([a-zA-Z])\1{2,}', r'\1', text)  
        
        return text.strip()
    except Exception as e:
        logger.error(f"OCR error: {str(e)}", exc_info=True)
        raise

def clean_text(text):
    """Enhanced text cleaning with line preservation"""
 
    text = re.sub(r'\s*-\s*', '-', text)
    
   
    text = re.sub(r'\b([A-Z])([A-Z]+)\b', lambda m: m.group(1) + m.group(2).lower(), text)
    
    
    text = re.sub(r'[^\wÀ-ỹ\s.,;:\-\n]', '', text, flags=re.UNICODE)
    
   
    text = '\n'.join([' '.join(line.split()) for line in text.split('\n')])
    
    return text.strip()



@login_required(login_url='/login/')
def upload_cover(request):
    if request.method == 'POST':
        form = BookCoverForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            try:
                img = Image.open(image)
                img = preprocess_image(img)
                raw_text = optimize_ocr_for_vietnamese(img)
                cleaned_title = clean_text(raw_text)

                if not cleaned_title:
                    return JsonResponse({'success': False, 'message': "Không thể nhận diện văn bản từ ảnh."})

                all_titles = list(Book.objects.values_list('title', flat=True))
                match = process.extractOne(cleaned_title, all_titles)

                if not match:
                    return JsonResponse({'success': False, 'message': "Không tìm thấy tiêu đề phù hợp."})

                best_match, _, _ = match
                books = Book.objects.filter(title__icontains=best_match)
                books_data = [{'title': b.title, 'author': b.author, 'id': b.id} for b in books]

                return render(request, 'result.html', {
                    'books': books,
                    'title': cleaned_title
                })

            except Exception as e:
                logger.error(f"Lỗi xử lý ảnh: {str(e)}", exc_info=True)
                return JsonResponse({'success': False, 'message': str(e)})
    return JsonResponse({'success': False, 'message': 'Yêu cầu không hợp lệ.'})



@require_POST
@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    if BorrowRecord.objects.filter(user=request.user, book=book, returned_at__isnull=True).exists():
        return JsonResponse({'success': False, 'message': f"Bạn đã mượn sách '{book.title}' rồi."})

    if book.quantity <= 0:
        return JsonResponse({'success': False, 'message': f"Sách '{book.title}' hiện không còn bản sao nào."})

    BorrowRecord.objects.create(
        user=request.user,
        book=book,
        borrowed_at=timezone.now()
    )

    book.quantity -= 1
    book.save()

    return JsonResponse({'success': True, 'message': f"Bạn đã mượn sách '{book.title}' thành công!"})
# View để liệt kê sách đã mượn
@login_required
def list_borrowed_books(request):
    borrowed_books = BorrowRecord.objects.filter(user=request.user, returned_at__isnull=True)
    return render(request, "borrowed_books.html", {"borrowed_books": borrowed_books})

# View để trả sách
@login_required
def return_book(request, borrow_id):
    borrow_record = get_object_or_404(BorrowRecord, id=borrow_id, user=request.user)

    if borrow_record.returned_at is None:
        borrow_record.returned_at = timezone.now()
        borrow_record.save()

        # Tăng lại số lượng sách
        book = borrow_record.book
        book.quantity += 1
        book.save()

        messages.success(request, f"Bạn đã trả sách '{book.title}' thành công!")
    else:
        messages.warning(request, "Sách này đã được trả trước đó.")

    return redirect("borrowed_books")