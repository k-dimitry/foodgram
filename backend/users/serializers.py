import base64
import uuid

from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.files.base import ContentFile
from rest_framework import serializers

from .models import Follow, User


class UserReadSerializer(serializers.ModelSerializer):
    """Пользователь: чтение (GET /users/, /users/{id}/, /users/me/)."""

    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'avatar',
        )
        read_only_fields = fields

    def get_is_subscribed(self, obj: User) -> bool:
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class UserCreateSerializer(serializers.ModelSerializer):
    """Пользователь: создание (POST /api/users/).

    Возвращает CustomUserResponseOnCreate: id, email, username,
    first_name, last_name (без avatar и is_subscribed).
    """

    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password',
        )
        read_only_fields = ('id',)

    def create(self, validated_data: dict) -> User:
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class TokenCreateSerializer(serializers.Serializer):
    """Логин: email + password → user (используется для получения токена)."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs: dict) -> dict:
        email = attrs.get('email')
        password = attrs.get('password')
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password,
        )
        if user is None:
            raise serializers.ValidationError(
                'Невозможно войти с предоставленными учетными данными.'
            )
        attrs['user'] = user
        return attrs


class SetPasswordSerializer(serializers.Serializer):
    """Смена пароля: current_password + new_password."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_current_password(self, value: str) -> str:
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Неверный текущий пароль.')
        return value

    def validate_new_password(self, value: str) -> str:
        validate_password(value, self.context['request'].user)
        return value

    def save(self, **kwargs) -> User:
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class AvatarSerializer(serializers.Serializer):
    """PUT /api/users/me/avatar/ — загрузка аватара (base64 в JSON)."""

    avatar = serializers.CharField(required=True, allow_blank=False)

    def validate_avatar(self, value: str) -> str:
        if not value.startswith('data:image/'):
            raise serializers.ValidationError(
                'Ожидается data-URI вида data:image/png;base64,...'
            )
        if ';base64,' not in value:
            raise serializers.ValidationError(
                'Ожидается base64-кодированное изображение.'
            )
        return value

    def save(self, **kwargs) -> User:
        user = self.context['request'].user
        data_uri = self.validated_data['avatar']

        header, b64_data = data_uri.split(';base64,', 1)
        ext = header.split('/')[-1].lower()
        if ext == 'jpeg':
            ext = 'jpg'

        try:
            decoded = base64.b64decode(b64_data)
        except Exception as exc:
            raise serializers.ValidationError(
                {'avatar': 'Не удалось декодировать base64.'}
            ) from exc

        filename = f'{uuid.uuid4().hex}.{ext}'
        user.avatar.save(filename, ContentFile(decoded), save=True)
        return user
