from rest_framework import serializers

from .hooks import VALIDATORS


def safe_str(obj):
    """str(obj), or None when a model's __str__ cannot cope with missing data."""
    if obj is None:
        return None
    try:
        return str(obj)
    except Exception:
        return None


def build_serializer(model):
    """Builds a plain ModelSerializer for `model`, exposing every field.
    FK/M2M fields serialize as their PK id(s) (DRF's default for
    fields='__all__') - no nested/expanded representations, keeping this
    generic across ~40 interlinked models without recursion/N+1 risk.
    FileField/ImageField values serialize as their absolute URL string
    (DRF's own default FileField behavior) - never the file content
    itself; downloading the actual bytes is a separate GET on that URL,
    which is already access-controlled (see core.views.media_download).

    Two read-only conveniences for API clients that cannot afford one
    request per id (e.g. an LLM): every row has a human readable `display`
    (the model's str()), and `?expand=employee,...` (validated by the
    viewset, passed in the serializer context) adds `<field>_display`."""
    meta = type('Meta', (), {'model': model, 'fields': '__all__'})

    def to_representation(self, instance):
        data = serializers.ModelSerializer.to_representation(self, instance)
        for name in self.context.get('expand', ()):
            value = getattr(instance, name)
            if model._meta.get_field(name).many_to_many:
                data[f'{name}_display'] = [safe_str(o) for o in value.all()]
            else:
                data[f'{name}_display'] = safe_str(value)
        return data

    attrs = {
        'Meta': meta,
        'display': serializers.SerializerMethodField(),
        'get_display': lambda self, obj: safe_str(obj),
        'to_representation': to_representation,
    }
    validator = VALIDATORS.get(model)
    if validator:
        # Models with UI-form validation (see hooks.py) get it applied here too.
        attrs['validate'] = lambda self, data: validator(self, data)
    return type(f'{model.__name__}Serializer', (serializers.ModelSerializer,), attrs)
