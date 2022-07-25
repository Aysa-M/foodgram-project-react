from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsObjectAuthorAuthUserAdminOrReadOnly(BasePermission):
    """
    Custom permissions for author|authorised user|admin to make
    manipulations with their own objects.
    """
    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS
            or request.user == obj.author
            or request.user.is_user
            or request.user.is_admin
        )


class IsAdmin(BasePermission):
    """
    Custom permissions for admin only to make
    manipulations with all the objects in the system.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsAuthorOnly(BasePermission):
    """
    Custom permissions for the author of the object to make any
    manipulations with it.
    """
    def has_permission(self, request, view):
        return (request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user)


class IsAuthorOrReadOnly(BasePermission):
    """
    Custom permissions for the author of the object to make any
    manipulations with it or read only otherwise.
    """
    def has_object_permission(self, request, view, obj):
        return (request.method in SAFE_METHODS
                or obj.author == request.user)
