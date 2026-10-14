# widgets.py
from django import forms
from django.utils.translation import gettext_lazy as _

class DatePickerInput(forms.DateInput):
    input_type = 'text'
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'datepicker',
            'placeholder': _('Select')
        }
        if attrs:
            default_attrs.update(attrs)

        super().__init__(
            attrs=default_attrs,
            format='%d/%m/%Y'
        )

class CustomFileInput(forms.FileInput):
    template_name = 'core/partials/file_input.html'
    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
    
        # Extract just the filename from the value
        if value:
            # value is typically a FieldFile object or string path
            filename = str(value).split('/')[-1]  # Gets last part after final /
            context['widget']['filename'] = filename
            context['widget']['has_file'] = True
        else:
            context['widget']['has_file'] = False
        
        return context