from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .registry import HR_ACCESS, MODELS, SEC_ACCESS
from .serializers import build_serializer
from .views import ADMIN, HR, SEC, build_viewset


def build_router(role, access_by_model, basename_prefix=''):
    router = DefaultRouter()
    # Distinct names so the three API root views can coexist.
    router.root_view_name = f'{basename_prefix}api-root'
    allowed = set(access_by_model)
    for model, access in access_by_model.items():
        app_label = model._meta.app_label
        model_name = model._meta.model_name
        router.register(
            f'{app_label}/{model_name}',
            build_viewset(model, build_serializer(model), role=role, access=access, allowed_models=allowed),
            basename=f'{basename_prefix}{app_label}_{model_name}',
        )
    return router


# /apiv2/<app>/<model>/      superuser, every model
# /apiv2/hr/<app>/<model>/   HR staff (and superuser)
# /apiv2/sec/<app>/<model>/  secretariats, limited to their scope (and superuser)
admin_router = build_router(ADMIN, {model: 'rw' for model in MODELS})
hr_router = build_router(HR, HR_ACCESS, 'hr_')
sec_router = build_router(SEC, SEC_ACCESS, 'sec_')

urlpatterns = [
    path('hr/', include(hr_router.urls)),
    path('sec/', include(sec_router.urls)),
] + admin_router.urls
