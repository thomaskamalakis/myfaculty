from rest_framework.permissions import SAFE_METHODS, BasePermission

from myprofile.checks import is_hr_user, is_secreteriat


class IsSuperUser(BasePermission):
    """Grants access only to authenticated Django superusers. This is the
    only notion of "admin" this codebase already has (see
    myprofile/checks.py's app_urls(), which treats is_superuser as
    "god access") - apiv2 deliberately doesn't invent a new role."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsHrRole(BasePermission):
    """HR staff (scopes.HrStaff) or superuser - same check as the HR UI."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and is_hr_user(request.user))


class IsSecretariatRole(BasePermission):
    """A secretariat with a non-empty scope, or superuser - same check as the UI."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_superuser or is_secreteriat(user)))


class IsReadOnly(BasePermission):
    """Used for the models a role may only read."""

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS
