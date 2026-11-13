from django.conf import settings


def google_login(request):
    """Tells the login/register templates whether to show 'Sign in with Google'."""
    return {'google_login_enabled': getattr(settings, 'GOOGLE_LOGIN_ENABLED', False)}
