from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import (
    AllowAny,
    BasePermission,
    IsAuthenticated,
)
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .serializers import (
    AvatarSerializer,
    SetPasswordSerializer,
    TokenCreateSerializer,
    UserCreateSerializer,
    UserReadSerializer,
)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Пользователи:

    - GET  /api/users/       — список (пагинация);
    - POST /api/users/       — регистрация;
    - GET  /api/users/{id}/  — профиль;
    - GET  /api/users/me/    — текущий пользователь (Token).
    """

    queryset = User.objects.all().order_by('id')

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        return UserReadSerializer

    def get_permissions(self) -> list[BasePermission]:
        if self.action == 'me':
            return [IsAuthenticated()]
        return super().get_permissions()

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request: Request) -> Response:
        """GET /api/users/me/ — текущий пользователь."""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class LoginView(APIView):
    """POST /api/auth/token/login/ — получить токен по email и паролю."""

    permission_classes = (AllowAny,)

    def post(self, request: Request) -> Response:
        serializer = TokenCreateSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'auth_token': token.key}, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """POST /api/auth/token/logout/ — удалить текущий токен."""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        Token.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SetPasswordView(APIView):
    """POST /api/users/set_password/ — сменить пароль текущего юзера."""

    permission_classes = (IsAuthenticated,)

    def post(self, request: Request) -> Response:
        serializer = SetPasswordSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AvatarView(APIView):
    """PUT / DELETE /api/users/me/avatar/ — аватар текущего пользователя."""

    permission_classes = (IsAuthenticated,)

    def put(self, request: Request) -> Response:
        serializer = AvatarSerializer(
            data=request.data,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        avatar_url = (
            request.build_absolute_uri(user.avatar.url)
            if user.avatar
            else None
        )
        return Response({'avatar': avatar_url}, status=status.HTTP_200_OK)

    def delete(self, request: Request) -> Response:
        user = request.user
        default_path = 'users/avatars/default.png'
        if user.avatar and user.avatar.name != default_path:
            user.avatar.delete(save=False)
        user.avatar = default_path
        user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)
