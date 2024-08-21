from django.shortcuts import render
from rest_framework import generics, viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, AuthorSerializer, BookSerializer, UserFavoriteSerializer
from django.contrib.auth.models import User
from .models import Author, UserFavorite, Book
from django.db.models import Q
from rest_framework.decorators import action
from libraryapi.utils import BookVectorizer
from pgvector.django import L2Distance
import numpy as np
# from django.db.models.expressions import RawSQL
# import json
# from django.db import connection


# Create your views here.
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

class LoginView(generics.GenericAPIView):
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")
        user = User.objects.filter(username=username).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })  
        return Response({"detail": "Invalid credentials"}, status=400)

class AuthorViewSet(viewsets.ModelViewSet):
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()

class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.AllowAny()]
        return super().get_permissions()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.query_params.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(authors__name__icontains=search_query)
            ).distinct()
        return queryset
    
    def create(self, request, *args, **kwargs):
        # Handle book creation
        data = request.data
        vectorizer = BookVectorizer()

        # Extract title and description from the request
        title = data.get('title', '')
        description = data.get('description', '')

        # Generate the vector using the title and description
        vector = vectorizer.generate_vector(title, description)

        # Create the book instance
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(vector=vector)

        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        # Handle book update
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data
        vectorizer = BookVectorizer()

        # Extract title and description from the request
        title = data.get('title', instance.title)
        description = data.get('description', instance.description)

        # Generate the vector using the title and description
        vector = vectorizer.generate_vector(title, description)

        # Update the book instance
        serializer = self.get_serializer(instance, data=data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save(vector=vector)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to reset the object cache.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)


class UserFavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = UserFavoriteSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        # Only return favorites for the current user
        return UserFavorite.objects.filter(user=self.request.user)

    @action(detail=False, methods=['post'])
    def add_favorite(self, request):
        user = request.user
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'error': 'Book ID is required'}, status=400)

        if UserFavorite.objects.filter(user=user).count() >= 20:
            return Response({'error': 'You can only have a maximum of 20 favorite books.'}, status=400)

        book = Book.objects.filter(id=book_id).first()
        if not book:
            return Response({'error': 'Book not found'}, status=404)

        favorite, created = UserFavorite.objects.get_or_create(user=request.user, book=book)
        if created:
            # Get all favorite books of the user
            favorite_books = UserFavorite.objects.filter(user=user).values_list('book', flat=True)
            favorite_book_vectors = Book.objects.filter(id__in=favorite_books).values_list('vector', flat=True)

            # Calculate the average vector of the favorite books
            avg_vector = np.mean(favorite_book_vectors, axis=0)
            similar_books = Book.objects.exclude(id__in=favorite_books).annotate(
                similarity=L2Distance('vector', avg_vector)
            ).order_by('similarity')[:5]
            
            # Create a list of dictionaries for the similar books
            book_values = similar_books.values('id', 'title', 'similarity')            
            return Response({
                'message': 'Book added to favorites',
                'top_similar_books': book_values
            }, status=201)

        return Response({'message': 'Book is already in favorites'}, status=200)

    @action(detail=False, methods=['post'])
    def remove_favorite(self, request):
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({'error': 'Book ID is required'}, status=400)

        favorite = UserFavorite.objects.filter(user=request.user, book_id=book_id).first()
        if not favorite:
            return Response({'error': 'Favorite not found'}, status=404)

        favorite.delete()
        return Response({'message': 'Book removed from favorites'}, status=204)

    @action(detail=False, methods=['get'])
    def list_favorites(self, request):
        favorites = self.get_queryset().select_related('book')
        data = [
            {
                'id': favorite.id,
                'user': favorite.user_id,
                'book_id': favorite.book_id,
                'book_title': favorite.book.title,
                'book_description': favorite.book.description,
                'added_on': favorite.added_on,
            }
            for favorite in favorites
        ]
        return Response(data)