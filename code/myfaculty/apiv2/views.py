from django.core.exceptions import FieldError, ValidationError
from rest_framework import viewsets
from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from rest_framework.exceptions import ParseError
from rest_framework.pagination import PageNumberPagination

from .permissions import IsSuperUser

# Query params reserved for pagination/DRF machinery - never treated as
# model-field filters.
RESERVED_QUERY_PARAMS = {'page', 'page_size', 'format'}


class ApiV2Pagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 500


def build_viewset(model, serializer_cls):
    """Builds a full-CRUD ModelViewSet for `model`: list/create/retrieve/
    update/partial_update/destroy, one instance at a time via the URL's
    <pk> (never a query param or request body), admin-only
    (IsSuperUser), and with the list/search behavior described in the
    plan: any query param not in RESERVED_QUERY_PARAMS is passed straight
    to queryset.filter(**kwargs) - Django's own "__" lookup syntax already
    gives dotted related-field filtering for free (e.g.
    ?user__username=jdoe&is_internal=True), matching a plain
    Model.objects.filter(...) call, nothing more complex. Deliberately
    bypasses the sc_filter/scope system entirely (Model.objects.all()) -
    an admin sees every row, no department/program filtering."""

    class GenericModelViewSet(viewsets.ModelViewSet):
        serializer_class = serializer_cls
        permission_classes = [IsSuperUser]
        # TokenAuthentication is already the project-wide default
        # (settings.REST_FRAMEWORK) - SessionAuthentication is added here
        # too so a superuser already logged into the site can use DRF's
        # browsable API directly without obtaining a token first.
        authentication_classes = [TokenAuthentication, SessionAuthentication]
        pagination_class = ApiV2Pagination

        def get_queryset(self):
            qs = model.objects.all()
            filters = {k: v for k, v in self.request.query_params.items() if k not in RESERVED_QUERY_PARAMS}
            if filters:
                try:
                    qs = qs.filter(**filters)
                except (FieldError, ValueError, ValidationError, TypeError) as e:
                    raise ParseError(f'Invalid filter parameters: {e}')
            return qs

    GenericModelViewSet.__name__ = f'{model.__name__}ViewSet'
    return GenericModelViewSet
