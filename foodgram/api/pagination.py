from rest_framework.pagination import PageNumberPagination


class FoodGramPagination(PageNumberPagination):
    """
    Custom pagination class with overset field, displaying
    quantity of objects.
    """
    page_size_query_param = 'limit'
