from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    uri = models.URLField(blank=True, null=True)
    collection = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='book_images/', null=True, blank=True)  

    def __str__(self):
        return self.title
    
#change form register

class CreateRegister(UserCreationForm):   
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']