from django.db.models import Case, When, Value, IntegerField

TITLE_ORDERINGS = [
    'Καθηγήτρια',
    'Καθηγητής',
    'Ομότιμος Καθηγητής', 
    'Associate Professor',
    'Αναπληρώτρια Καθηγήτρια',
    'Αναπλ. Καθηγητής',
    'Αναπληρωτής Καθηγητής',
    'Επίκουρη Καθηγήτρια',
    'Επίκουρος Καθηγητής',
    'Λέκτορας',
    'Εντεταλμένος Ερευνητής',
    'Εξωτερικός Συνεργάτης',
    'Εξωτερική Διδάσκεων',
    'Εξωτερικός Διδάσκων',
    'Εξωτερικός Διδάσκοντας',
    'ΕΤΕΠ',
    'ΕΔΙΠ',
]

def sort_by_title(queryset):
    whens = [
        When(title=title, then=Value(index))
        for index, title in enumerate(TITLE_ORDERINGS)
    ]

    return queryset.annotate(
        _title_order=Case(
            *whens,
            default=Value(len(TITLE_ORDERINGS)),
            output_field=IntegerField(),
        )
    ).order_by('_title_order', 'surname')