from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Div, Field, HTML
from datetime import date
from .widgets import DatePickerInput, CustomFileInput

class GenericForm(forms.Form):

    config = {
        'labels' : {},
        'help_texts' : {},
    }

    date_picker = True
    scoped_fields = []
    disabled_fields = []
    disabled = False
    date_format = '%d/%m/%Y'
    date_help_text = _('Κάντε click στο πεδίο και επιλέξτε.')
    date_help_text_no_picker = _('Χρησιμοποιήστε τη μορφή DD/MM/YYYY, π.χ. 21/01/2026')
    submit_button_text = _('Υποβολή')
    submit_button_icon = 'save'
    submit_button = True
    heading = ''
    required_fields_extra = []
    initial_values = {}
    required_all = False
    form_id = 'crispyForm'
    form_tag = True
    button_element = """
                    <div class = "col-lg-12 text-end">
                    <button type="submit" class="btn btn-primary submit-button">
                    <span class="mto"> %s </span> %s
                    </button>
                    </div>
                    """ 
    class Meta:
        labels = None
        fields = '__all__'
        model = None

    def disable_form_fields(self, fields = None):
        if not fields:
            fields = self.disabled_fields

        for field_name in fields:
            if field_name in self.fields:
                self.fields[field_name].disabled = True
    
    def __init__(self, *args, querysets = None, **kwargs):

        self.required_all = kwargs.pop('required_all', self.required_all)
        self.user = kwargs.pop('user', None)
        self.initial_values = kwargs.pop('initial_values', self.initial_values)
        self.required_fields_extra = kwargs.pop('required_fields_extra', self.required_fields_extra)        
        self.submit_button_icon = kwargs.pop('submit_button_icon', self.submit_button_icon)
        self.submit_button_text = kwargs.pop('submit_button_text', self.submit_button_text)
        self.disabled = kwargs.pop('disabled', self.disabled)
        self.disabled_fields = kwargs.pop('disabled_fields', self.disabled_fields)
        self.form_id = kwargs.pop('form_id', self.form_id)
        self.date_picker = kwargs.pop('date_picker', self.date_picker)
        self.form_tag = kwargs.pop('form_tag', self.form_tag)

            
        super().__init__(*args, **kwargs)

        if 'labels' in self.config:
            labels = self.config['labels']
            for n, v in labels.items():
                if n in self.fields:
                    self.fields[n].label = v

        if 'help_texts' in self.config:
            help_texts = self.config['help_texts']
            for n, v in help_texts.items():
                if n in self.fields:
                    self.fields[n].help_text = v
                    
        if self.disabled:
            self.disabled_fields = list(self.fields.keys())
        
        if self.required_all:
            self.required_fields_extra = list(self.fields.keys())
        

        self.disable_form_fields(fields = self.disabled_fields)
        
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DateField):
                field.input_formats = [self.date_format]
                field.widget.format = self.date_format
                if self.date_picker:
                    field.widget = DatePickerInput()
                    field.help_text = self.date_help_text
                else:
                    field.help_text = self.date_help_text_no_picker
                
        
        for field_name in self.scoped_fields:
            form_model = self._meta.model
            attribute = getattr(form_model, field_name)
            related_model = attribute.field.related_model
            field.queryset = related_model.objects.sc_filter(user=self.user)

        for field_name in self.required_fields_extra:
            self.fields[field_name].required = True

        for field_name, initial_value in self.initial_values.items():
            self.fields[field_name].initial = initial_value
    
        if querysets is not None:
            for field_name, queryset in querysets.items():
                self.fields[field_name].queryset = queryset

        self.heading_html = HTML('<h4> ' +self.heading + ' </h4>')
        layout = Layout( Row( Div( self.heading_html, css_class = 'col-lg-8'),
                            css_class="row" ) )

        if not self.disabled and self.submit_button:
            self.button_element_html = HTML( self.button_element %(self.submit_button_icon, self.submit_button_text ) )
            layout.append( Row( self.button_element_html, css_class="row" ) ) 
            
        for field in self.fields:
            if isinstance(self.fields[field], forms.FileField):
                layout.append( Row( Div( Field( field, template="core/partials/file_input.html" ), css_class="row" ) ) )
            else:
                layout.append( Row( Div( Field( field ), css_class="row" ) ) )

        self.helper = FormHelper()
        self.helper.layout = layout
        self.helper.form_id = self.form_id
        self.helper.form_tag = self.form_tag
        
class GenericModelForm(forms.ModelForm):

    date_picker = True
    scoped_fields = []
    disabled_fields = []
    disabled = False
    date_format = '%d/%m/%Y'
    date_help_text = _('Κάντε click στο πεδίο και επιλέξτε.')
    date_help_text_no_picker = _('Χρησιμοποιήστε τη μορφή DD/MM/YYYY, π.χ. 21/01/2026')
    submit_button_text = _('Υποβολή')
    submit_button_icon = 'save'
    submit_button = True
    heading = ''
    required_fields_extra = []
    initial_values = {}
    required_all = False
    form_id = 'crispyForm'
    form_tag = True
    button_element = """
                    <div class = "col-lg-12 text-end">
                    <button type="submit" class="btn btn-primary submit-button">
                    <span class="mto"> %s </span> %s
                    </button>
                    </div>
                    """ 
    class Meta:
        labels = None
        fields = '__all__'
        model = None

    def disable(self):
        for field_name in self.fields:
            self.fields[field_name].disabled = True
    
    def disable_form_fields(self, fields = None):
        if not fields:
            fields = self.disabled_fields

        for field_name in fields:
            if field_name in self.fields:
                self.fields[field_name].disabled = True
    
    def __init__(self, *args, querysets = None, **kwargs):

        self.required_all = kwargs.pop('required_all', self.required_all)
        self.user = kwargs.pop('user', None)
        self.initial_values = kwargs.pop('initial_values', self.initial_values)
        self.required_fields_extra = kwargs.pop('required_fields_extra', self.required_fields_extra)        
        self.submit_button_icon = kwargs.pop('submit_button_icon', self.submit_button_icon)
        self.submit_button_text = kwargs.pop('submit_button_text', self.submit_button_text)
        self.disabled = kwargs.pop('disabled', self.disabled)
        self.disabled_fields = kwargs.pop('disabled_fields', self.disabled_fields)
        self.form_id = kwargs.pop('form_id', self.form_id)
        self.date_picker = kwargs.pop('date_picker', self.date_picker)
        self.form_tag = kwargs.pop('form_tag', self.form_tag)

        super().__init__(*args, **kwargs)
        
         
        if self.disabled:
            self.disabled_fields = list(self.fields.keys())
        
        if self.required_all:
            self.required_fields_extra = list(self.fields.keys())
        

        self.disable_form_fields(fields = self.disabled_fields)
        
        for field_name, field in self.fields.items():
            if isinstance(field, forms.DateField):
                field.input_formats = [self.date_format]
                field.widget.format = self.date_format
                if self.date_picker:
                    field.widget = DatePickerInput()
                    field.help_text = self.date_help_text
                else:
                    field.help_text = self.date_help_text_no_picker
                
        
        for field_name in self.scoped_fields:
            form_model = self._meta.model
            attribute = getattr(form_model, field_name)
            related_model = attribute.field.related_model
            field.queryset = related_model.objects.sc_filter(user=self.user)

        for field_name in self.required_fields_extra:
            self.fields[field_name].required = True

        for field_name, initial_value in self.initial_values.items():
            self.fields[field_name].initial = initial_value
    
        if querysets is not None:
            for field_name, queryset in querysets.items():
                self.fields[field_name].queryset = queryset

        self.heading_html = HTML('<h4> ' +self.heading + ' </h4>')
        layout = Layout( Row( Div( self.heading_html, css_class = 'col-lg-8'),
                            css_class="row" ) )

        if not self.disabled and self.submit_button:
            self.button_element_html = HTML( self.button_element %(self.submit_button_icon, self.submit_button_text ) )
            layout.append( Row( self.button_element_html, css_class="row" ) ) 
            
        for field in self.fields:
            if isinstance(self.fields[field], forms.FileField):
                layout.append( Row( Div( Field( field, template="core/partials/file_input.html" ), css_class="row" ) ) )
            else:
                layout.append( Row( Div( Field( field ), css_class="row" ) ) )

        self.helper = FormHelper()
        self.helper.layout = layout
        self.helper.form_id = self.form_id
        self.helper.form_tag = self.form_tag

    def save(self, commit=True):
        instance = super().save(commit=False)
        if hasattr(instance, 'created_by') and hasattr(instance, 'updated_by'):
            if not instance.pk:
                instance.created_by = self.user
            instance.updated_by = self.user
        if commit:
            instance.save()
            self.save_m2m()
        return instance    
    

