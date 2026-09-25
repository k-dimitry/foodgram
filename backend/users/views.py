from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Follow, User
from .serializers import (
    AvatarSerializer,
    UserReadSerializer,
    UserWithRecipesSerializer,
)


class UserViewSet(DjoserUserViewSet):
    """Расширяем Djoser-UserViewSet: аватар, подписки, me с 401.

    Всё остальное (create/list/retrieve/set_password/me) — из Djoser.
    """

    queryset = User.objects.all()

    @action(
        detail=False,
        methods=('get',),
        url_path='me',
        permission_classes=(IsAuthenticated,),
    )
    def me(self, request: Request) -> Response:
        """GET /api/users/me/ — текущий пользователь.

        Переопределено ради permission: у Djoser `me` берёт
        PERMISSIONS['user'] (= AllowAny у нас), поэтому аноним
        получал 200. Возвращаем 401.
        """
        serializer = UserReadSerializer(
            request.user,
            context={'request': request},
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(
        detail=False,
        methods=('put', 'delete'),
        url_path='me/avatar',
        permission_classes=(IsAuthenticated,),
    )
    def avatar(self, request: Request) -> Response:
        """PUT / DELETE /api/users/me/avatar/
        аватар текущего пользователя.
        """
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                request.user,
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
            return Response(
                {'avatar': avatar_url},
                status=status.HTTP_200_OK,
            )

        user = request.user
        if user.avatar:
            user.avatar.delete(save=False)
        user.avatar = None
        user.save(update_fields=['avatar'])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=('post', 'delete'),
        url_path='subscribe',
        permission_classes=(IsAuthenticated,),
    )
    def subscribe(self, request, *args, **kwargs) -> Response:
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
                author,
                context={'request': request},
            )
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED,
            )

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
    def subscriptions(self, request: Request) -> Response:
        """GET /api/users/subscriptions/ — кого читает текущий пользователь."""
        authors = User.objects.filter(subscribers__user=request.user).order_by(
            'username'
        )
        page = self.paginate_queryset(authors)
        serializer = UserWithRecipesSerializer(
            page,
            many=True,
            context={'request': request},
        )
        return self.get_paginated_response(serializer.data)
