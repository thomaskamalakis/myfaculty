from django.conf import settings
from django.utils.translation import get_language

def get_lang():
    return (get_language() or settings.LANGUAGE_CODE)[:2]

# Create or update an object:
#  -obj_class is the object model class
#  -d is a dictionary with model attribute values
#  -kwargs contais the parameters of a queryDict to check if the model exists

def create_or_update_obj(obj_class, d, **kwargs):
    print('Querying:', kwargs)
    obj = obj_class.objects.filter(**kwargs)
    
    if obj.exists():
        print(f'Object of class {obj_class} exists')
        obj = obj.first()
    else:
        print(f'Object of class {obj_class} does not exist')
        obj = obj_class()
    
    for k, v in d.items():
        if hasattr(obj, k):
            setattr(obj,k,v)
    obj.save()
    return obj

def update_obj(obj, d):
    for k, v in d.items():
        if hasattr(obj, k):
            setattr(obj,k,v)

    obj.save()
    return obj