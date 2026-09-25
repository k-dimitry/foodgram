"""Утилиты приложения recipes."""

import base64
import uuid

from django.core.files.base import ContentFile
from rest_framework import serializers


def decode_base64_image(data_uri: str) -> ContentFile:
    """Декодирует data:image/...;base64,... → ContentFile для ImageField."""
    if not isinstance(data_uri, str) or not data_uri.startswith('data:image/'):
        raise serializers.ValidationError(
            'Ожидается data-URI вида data:image/png;base64,...'
        )
    if ';base64,' not in data_uri:
        raise serializers.ValidationError(
            'Ожидается base64-кодированное изображение.'
        )
    header, b64_data = data_uri.split(';base64,', 1)
    ext = header.split('/')[-1].lower()
    if ext == 'jpeg':
        ext = 'jpg'
    try:
        decoded = base64.b64decode(b64_data)
    except Exception as exc:
        raise serializers.ValidationError(
            'Не удалось декодировать base64.'
        ) from exc
    filename = f'{uuid.uuid4().hex}.{ext}'
    return ContentFile(decoded, name=filename)
