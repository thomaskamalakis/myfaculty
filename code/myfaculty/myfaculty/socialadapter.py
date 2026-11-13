from allauth.core.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from myprofile.models import create_user_if_required

UserModel = get_user_model()


def _reject(request, message):
    messages.error(request, message)
    raise ImmediateHttpResponse(redirect('login'))


class GoogleAdapter(DefaultSocialAccountAdapter):
    """
    Google is an alternative way to log in. Google has already verified the
    email, so no further verification is needed. An existing user (internal
    @hua.gr via LDAP, or external registered the old way) is matched by email and
    linked; otherwise a user is created using the same username scheme as
    myprofile.models.create_user_if_required.
    """

    def is_open_for_signup(self, request, sociallogin):
        return settings.GOOGLE_LOGIN_ENABLED

    @staticmethod
    def _verified_email(sociallogin):
        """Return the lower-cased Google email if Google says it is verified, else None."""
        for address in sociallogin.email_addresses:
            if address.email and address.verified:
                return address.email.strip().lower()
        return None

    def pre_social_login(self, request, sociallogin):
        if not settings.GOOGLE_LOGIN_ENABLED:
            _reject(request, _('Η σύνδεση με Google δεν είναι ενεργή.'))
        email = self._verified_email(sociallogin)
        if not email:
            _reject(request, _('Η Google δεν επιβεβαίωσε το email σας. Δεν είναι δυνατή η σύνδεση.'))

        # Already linked to a user: just make sure the account is usable
        if sociallogin.is_existing:
            if not sociallogin.user.is_active:
                _reject(request, _('Ο λογαριασμός σας είναι απενεργοποιημένος.'))
            return

        users = list(UserModel.objects.filter(email__iexact=email))
        if not users:
            # LDAP users may exist without an email stored; match by username
            # (same scheme as create_user_if_required)
            local, _sep, domain = email.partition('@')
            lookup = local if domain == settings.INTERNAL_DOMAIN else email
            users = list(UserModel.objects.filter(username__iexact=lookup))
        if len(users) > 1:
            _reject(request, _('Βρέθηκαν περισσότεροι από ένας λογαριασμοί με αυτό το email. Επικοινωνήστε με τη γραμματεία.'))
        if users:
            user = users[0]
            if not user.is_active:
                _reject(request, _('Ο λογαριασμός σας είναι απενεργοποιημένος.'))
            sociallogin.connect(request, user)

    def save_user(self, request, sociallogin, form=None):
        """Create a new user with the same username scheme as the rest of the app."""
        email = self._verified_email(sociallogin)
        user = create_user_if_required(email)
        data = sociallogin.account.extra_data or {}
        if not user.first_name:
            user.first_name = data.get('given_name', '')
        if not user.last_name:
            user.last_name = data.get('family_name', '')
        user.email = email
        if not user.password:
            user.set_unusable_password()
        user.save()
        sociallogin.user = user
        sociallogin.save(request)
        return user
