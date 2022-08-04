from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permissions for admin to make
    manipulations with objects.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user.is_admin
        )


class IsAuthorOnly(BasePermission):
    """
    Custom permissions for the author of the object to make any
    manipulations with it.
    """
    def has_permission(self, request, view):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        if obj.user == request.user:
            return True
        return False
