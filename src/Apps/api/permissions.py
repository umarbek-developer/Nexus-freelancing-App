"""
Custom DRF permission classes for role-based access control.
"""
from rest_framework.permissions import BasePermission


class IsClient(BasePermission):
    """Allow access only to users with role='client'."""
    message = 'Bu amal faqat mijozlar (client) uchun mavjud.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'client'
        )


class IsFreelancer(BasePermission):
    """Allow access only to users with role='freelancer'."""
    message = 'Bu amal faqat freelancerlar uchun mavjud.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'freelancer'
        )


class IsClientOrFreelancer(BasePermission):
    """Allow any authenticated user with a known role."""
    message = 'Foydalanuvchi roli aniqlanmagan.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('client', 'freelancer')
        )
