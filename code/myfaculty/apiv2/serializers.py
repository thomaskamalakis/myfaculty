from rest_framework import serializers


def build_serializer(model):
    """Builds a plain ModelSerializer for `model`, exposing every field.
    FK/M2M fields serialize as their PK id(s) (DRF's default for
    fields='__all__') - no nested/expanded representations, keeping this
    generic across ~36 interlinked models without recursion/N+1 risk.
    FileField/ImageField values serialize as their absolute URL string
    (DRF's own default FileField behavior) - never the file content
    itself; downloading the actual bytes is a separate GET on that URL,
    which is already access-controlled (see core.views.media_download)."""
    meta = type('Meta', (), {'model': model, 'fields': '__all__'})
    return type(f'{model.__name__}Serializer', (serializers.ModelSerializer,), {'Meta': meta})
