from rest_framework import mixins, viewsets


class ListViewSet(mixins.ListModelMixin,
                  viewsets.GenericViewSet):
    """
    Custom viewset for processing GET-requests which returns the list
    of objects as a response.
    """
    pass


class ListRetrieveViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          viewsets.GenericViewSet):
    """
    Custom viewset for processing GET-requests which returns the list
    of objects or some current object as a response.
    """
    pass
