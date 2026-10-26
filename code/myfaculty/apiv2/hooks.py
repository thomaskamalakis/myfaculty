"""
Business logic that the Django UI runs in its views/forms and that a plain
ModelSerializer would skip. Called explicitly by the apiv2 viewsets (no
signals): validation before saving, and recalculations after saving or
deleting.
"""
from rest_framework import serializers

from hrms import models as hrms_models
from hrms.views import FORM_APP_FLAG

Application = hrms_models.Application
Decision = hrms_models.Decision
PayrollDecision = hrms_models.PayrollDecision


def validate_application(serializer, attrs):
    """Runs the same per-type form the UI and the Excel import use, so that
    the API enforces identical rules (required fields per type, no future
    dates, dates before date_hired, ...)."""
    instance = serializer.instance

    def get(name):
        if name in attrs:
            return attrs[name]
        return getattr(instance, name, None) if instance else None

    app_type = get('type')
    form_class = FORM_APP_FLAG.get(app_type)
    if form_class is None:
        raise serializers.ValidationError({'type': 'Unknown application type.'})
    if not get('start_date') or not get('end_date'):
        raise serializers.ValidationError('start_date and end_date are required.')

    data = {}
    for name in form_class._meta.fields:
        if Application._meta.get_field(name).get_internal_type() == 'FileField':
            continue
        value = get(name)
        if value is None:
            continue
        if hasattr(value, 'strftime'):
            # the forms parse dates with core.forms.GenericModelForm.date_format
            value = value.strftime('%d/%m/%Y')
        data[name] = value
    # The external-experience form takes a 0-100 percentage and divides by 100 itself.
    if app_type == Application.EXTERNAL and 'day_percentage' in data:
        data['day_percentage'] = float(data['day_percentage']) * 100

    form = form_class(data, employee=get('employee'))
    if not form.is_valid():
        raise serializers.ValidationError(
            {name: [str(e) for e in errors] for name, errors in form.errors.items()})
    return attrs


# model -> function(serializer, attrs) run in Serializer.validate()
VALIDATORS = {
    Application: validate_application,
}


def _app_after_save(instance):
    Decision.recalc_many(Decision.affected_by([instance]))


def _decision_after_save(instance):
    instance.calc()
    instance.save()


def _payroll_after_save(instance):
    if instance.decision_type == PayrollDecision.PRIOR_SERVICE_RECOGNITION:
        instance.sync_from_linked_decision()
        instance.save()


AFTER_SAVE = {
    Application: _app_after_save,
    Decision: _decision_after_save,
    PayrollDecision: _payroll_after_save,
}


def before_delete(instance):
    """State to carry over to after_delete (must be captured before the
    row and its M2M links disappear)."""
    if isinstance(instance, Application):
        return Decision.affected_by([instance])
    return None


def after_delete(instance, state):
    if isinstance(instance, Application):
        Decision.recalc_many(state)


def after_save(instance):
    hook = AFTER_SAVE.get(type(instance))
    if hook:
        hook(instance)
