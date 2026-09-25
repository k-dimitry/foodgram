from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAuthorOrReadOnly(BasePermission):
    """Чтение — всем, изменение — только автору объекта."""

    message = 'У вас недостаточно прав для выполнения данного действия.'

    def has_object_permission(self, request, view, obj) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return obj.author == request.user
