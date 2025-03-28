from django.db import models

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    uri = models.URLField(blank=True, null=True)
    collection = models.CharField(max_length=255, blank=True, null=True)
    image = models.ImageField(upload_to='book_images/', null=True, blank=True)  

    def __str__(self):
        return self.title