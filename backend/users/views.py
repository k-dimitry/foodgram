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

from .models import Follow, User
from .serializers import (
    AvatarSerializer,
    SetPasswordSerializer,
    TokenCreateSerializer,
    UserCreateSerializer,
    UserReadSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
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

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, pk=None):
        """POST — подписаться, DELETE — отписаться."""
        author = self.get_object()

        if author == request.user:
            return Response(
                {'detail': 'Нельзя подписаться на себя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if request.method == 'POST':
            _, created = Follow.objects.get_or_create(
                user=request.user,
                author=author,
            )
            if not created:
                return Response(
                    {'detail': 'Вы уже подписаны на этого пользователя.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = UserWithRecipesSerializer(
                author, context={'request': request},
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        deleted, _ = Follow.objects.filter(
            user=request.user,
            author=author,
        ).delete()
        if not deleted:
            return Response(
                {'detail': 'Вы не подписаны на этого пользователя.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=('get',),
        url_path='subscriptions',
        permission_classes=(IsAuthenticated,),
    )
    def subscriptions(self, request):
        """GET /api/users/subscriptions/ — кого читает текущий пользователь."""
        authors = (
            User.objects
            .filter(subscribers__user=request.user)
            .order_by('id')
        )
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request},
        )
        return self.get_paginated_response(serializer.data)


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
        if user.avatar:
            user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)
