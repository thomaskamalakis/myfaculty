from rest_framework.routers import DefaultRouter

from .registry import MODELS
from .serializers import build_serializer
from .views import build_viewset

router = DefaultRouter()
for model in MODELS:
    app_label = model._meta.app_label
    model_name = model._meta.model_name
    router.register(
        f'{app_label}/{model_name}',
        build_viewset(model, build_serializer(model)),
        basename=f'{app_label}_{model_name}',
    )

urlpatterns = router.urls
