from rest_framework.permissions import BasePermission


class IsSuperUser(BasePermission):
    """Grants access only to authenticated Django superusers. This is the
    only notion of "admin" this codebase already has (see
    myprofile/checks.py's app_urls(), which treats is_superuser as
    "god access") - apiv2 deliberately doesn't invent a new role."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)
