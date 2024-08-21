from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField

class Author(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(blank=True)
    about = models.TextField(blank=True)
    ratings_count = models.IntegerField(default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    text_reviews_count = models.IntegerField(default=0)
    fans_count = models.IntegerField(default=0)
    works_count = models.IntegerField(default=0)

    def __str__(self):
        return self.name
    
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]

class Book(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    authors = models.ManyToManyField(Author, related_name='books')
    work_id = models.CharField(max_length=255, blank=True)
    isbn = models.CharField(max_length=13, blank=True)
    isbn13 = models.CharField(max_length=13, blank=True)
    asin = models.CharField(max_length=10, blank=True)
    language = models.CharField(max_length=100)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    ratings_count = models.IntegerField(default=0)
    text_reviews_count = models.IntegerField(default=0)
    publication_date = models.DateField(null=True, blank=True)
    original_publication_date = models.DateField(null=True, blank=True)
    format = models.CharField(max_length=50, blank=True)
    edition_information = models.CharField(max_length=255, blank=True)
    image_url = models.URLField(blank=True)
    publisher = models.CharField(max_length=255, blank=True)
    num_pages = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    rating_distribution = models.OneToOneField(
        'RatingDistribution',
        on_delete=models.CASCADE,
        related_name='book',
        null=True,
        blank=True
    )
    vector = VectorField(dimensions=384, null=True, blank=True)
    def __str__(self):
        return self.title

    class Meta:
        indexes = [
            models.Index(fields=['title']),
        ]

class RatingDistribution(models.Model):    
    rating_5 = models.IntegerField(default=0)
    rating_4 = models.IntegerField(default=0)
    rating_3 = models.IntegerField(default=0)
    rating_2 = models.IntegerField(default=0)
    rating_1 = models.IntegerField(default=0)
    total = models.IntegerField(default=0)

    def __str__(self):
        return f"Distribution for Book ID {self.book.id}"

class UserFavorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='favorited_by')
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'book')

    def __str__(self):
        return f'{self.user.username} - {self.book.title}'
