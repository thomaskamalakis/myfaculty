from django.utils import translation
from django.views.generic import TemplateView


class LegalPage(TemplateView):
    """
    Public (no login) legal pages. They live outside i18n_patterns so the URL
    given to Google's OAuth consent screen is fixed; the language follows the
    usual session/cookie/browser detection and can be forced with ?lang=el|en.
    """

    def dispatch(self, request, *args, **kwargs):
        lang = request.GET.get('lang')
        if lang in ('el', 'en'):
            translation.activate(lang)
            request.LANGUAGE_CODE = lang
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # the i18n context processor is not enabled in settings
        context['LANGUAGE_CODE'] = (translation.get_language() or 'el')[:2]
        return context
