from rest_framework.pagination import PageNumberPagination


class LimitPageNumberPagination(PageNumberPagination):
    """PageNumberPagination + поддержка ?limit=N (для Postman-коллекции)."""

    page_size_query_param = 'limit'
    max_page_size = 100
