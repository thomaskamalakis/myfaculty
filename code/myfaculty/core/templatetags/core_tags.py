from django import template
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.utils.safestring import mark_safe
from core.views import DEFAULT_CONTEXT_VALUES
from pathlib import Path
from django.utils.translation import get_language
from django.db.models import CharField, TextField
from core.utils import get_lang

register = template.Library()

@register.filter
def index(sequence, i):
    try:
        return sequence[int(i)]
    except (IndexError, TypeError, ValueError):
        return ""
    
@register.filter
def get_attr(obj, attr):
    """
    Supports dotted paths and callables: 'candidate.program.title'
    """
    lang = get_language()[:2]

    for part in attr.split("."):
        if obj is None:
            return ""

        prev_obj = obj
        obj = getattr(obj, part, "")
        
        if callable(obj):
            obj = obj()

    # Check for translation
    if isinstance(obj, str) and part:
        
        if lang == 'en':
            new_part = part + '_en'
            if hasattr(prev_obj, new_part):
                return get_attr(prev_obj, new_part)
            
            elif part.endswith('_gr'):
                new_part = part.split('_gr')[0] + '_en'
                if hasattr(prev_obj, new_part):
                    return getattr(prev_obj, new_part)
                
    return obj

@register.filter
def get_item(d, key):
    return d.get(key)

@register.filter
def get_items(d):
    keys, vals = d.items()
    return vals

@register.inclusion_tag("core/partials/table.html", takes_context=True)
def render_table(context, table):
    table_context = {}
    for key in DEFAULT_CONTEXT_VALUES.keys():
        table_context[key] = table.get(key, '')
    # Χρειάζεται για πίνακες με φόρμα POST (π.χ. μαζική διαγραφή)
    table_context['csrf_token'] = context.get('csrf_token', '')
    return table_context

@register.filter
def get_filename(s):
    filename = str(s.value()).split('/')[-1]
    if len(filename) > 20:
        filename = filename[0:16] + '...'
    return filename
# def render_table(table):

#     objects = table['objects']
#     table_id = table['table_id']
#     fields = table['fields'] 
#     headers = table['headers']
#     button_texts = table['button_texts']
#     button_classes = table['button_classes']
#     button_urls = table['button_urls']
    
#     # Table head
#     html =  f'<table id="{table_id}"<thead><tr>'
#     for field in fields:
#         html += f"<th>{headers[field]}</th>"
#     for button in button_texts:
#         html += f"<th></th>"
#     html += "</tr></thead>"

#     # Table rows
#     html += '<tbody>'
#     for i, object in enumerate(objects):
#         html += '<tr>'
#         for field in fields:
#             html += f'<td>{get_attr(object,field)}</td>'
#         for j, button_text in enumerate(button_texts):
#             html += f'<td><a href="{button_urls[i][j]} class="{button_classes[j]}">{button_text[j]}</td>'

#         html += '</tr>'
#     html += '</tbody></table>'
    
#     return mark_safe(html)
