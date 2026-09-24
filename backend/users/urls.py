from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    AvatarView,
    LoginView,
    LogoutView,
    SetPasswordView,
    UserViewSet,
)


router = DefaultRouter()
router.register('users', UserViewSet, basename='user')

urlpatterns = [
    path('auth/token/login/', LoginView.as_view(), name='login'),
    path('auth/token/logout/', LogoutView.as_view(), name='logout'),
    path(
        'users/set_password/', SetPasswordView.as_view(), name='set-password'
    ),
    path('users/me/avatar/', AvatarView.as_view(), name='avatar'),
]

urlpatterns += router.urls
