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


class ListCreateDestroyViewSet(mixins.ListModelMixin,
                               mixins.CreateModelMixin,
                               mixins.DestroyModelMixin,
                               viewsets.GenericViewSet):
    """
    Custom viewset for processing:
    GET-request provides the list of objects,
    POST-request provides creation of a new model object,
    DEL-request provides destroying a current model object.
    """
    pass


class CreateDestroyViewSet(mixins.CreateModelMixin,
                           mixins.DestroyModelMixin,
                           viewsets.GenericViewSet):
    """
    Custom viewset for processing:
    POST-request provides creation of a new model object,
    DEL-request provides destroying a current model object.
    """
    pass
