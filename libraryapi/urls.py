from django.urls import path, include
from .views import RegisterView, LoginView, AuthorViewSet, BookViewSet, UserFavoriteViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'authors', AuthorViewSet)
router.register(r'books', BookViewSet, basename='book')
router.register(r'favorites', UserFavoriteViewSet, basename='favorite')

urlpatterns = [
    path('', include(router.urls)),
    path('register', RegisterView.as_view(), name='register'),
    path('login', LoginView.as_view(), name='login'),
]