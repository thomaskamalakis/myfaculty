"""Πρακτικό αναγνώρισης προϋπηρεσίας (Word) από μια απόφαση (Decision).

Ο υπολογισμός του χρόνου και των επικαλύψεων γίνεται από τα υπάρχοντα Decision.calc / interval_map
(σε επίπεδο ημέρας). Εδώ γίνεται μόνο ταξινόμηση, ομαδοποίηση και μορφοποίηση για το έγγραφο.
"""
import io
from datetime import timedelta
from pathlib import Path

from docxtpl import DocxTemplate

from .utils import calc_ymd
from .work_intervals import interval_map

TEMPLATE_PATH = Path(__file__).resolve().parent / 'docx_templates' / 'recognition_minutes.docx'

EMPTY = '……'

_UNITS_NOM = ['μηδέν', 'ένα', 'δύο', 'τρία', 'τέσσερα', 'πέντε', 'έξι', 'επτά', 'οκτώ', 'εννέα']
_UNITS_GEN = {
    1: {'m': 'ενός', 'f': 'μίας', 'n': 'ενός'},
    3: 'τριών',
    4: 'τεσσάρων',
}
_TEENS = {
    10: 'δέκα', 11: 'έντεκα', 12: 'δώδεκα', 13: 'δεκατριών', 14: 'δεκατεσσάρων', 15: 'δεκαπέντε',
    16: 'δεκαέξι', 17: 'δεκαεπτά', 18: 'δεκαοκτώ', 19: 'δεκαεννέα',
}
_TENS = {2: 'είκοσι', 3: 'τριάντα', 4: 'σαράντα', 5: 'πενήντα', 6: 'εξήντα', 7: 'εβδομήντα', 8: 'ογδόντα', 9: 'ενενήντα'}


def _unit_genitive(n, gender):
    if n in _UNITS_GEN and isinstance(_UNITS_GEN[n], dict):
        return _UNITS_GEN[n][gender]
    return _UNITS_GEN.get(n) or _UNITS_NOM[n]


def number_genitive(n, gender='n'):
    """Ο αριθμός (0-99) ολογράφως σε γενική: 12 -> «δώδεκα», 21 (θηλυκό) -> «είκοσι μίας»."""
    n = int(n)
    if n < 10:
        return _unit_genitive(n, gender) if n else _UNITS_NOM[0]
    if n < 20:
        return _TEENS[n]
    if n < 100:
        tens, unit = divmod(n, 10)
        return _TENS[tens] if unit == 0 else f'{_TENS[tens]} {_unit_genitive(unit, gender)}'
    return str(n)


def duration_in_words(years, months, days):
    """«δώδεκα (12) ετών, έντεκα (11) μηνών και δεκαπέντε (15) ημερών»."""
    parts = [
        _with_unit(years, 'n', 'έτους', 'ετών'),
        _with_unit(months, 'm', 'μηνός', 'μηνών'),
        _with_unit(days, 'f', 'ημέρας', 'ημερών'),
    ]
    return f'{parts[0]}, {parts[1]} και {parts[2]}'


def _with_unit(n, gender, singular, plural):
    return f'{number_genitive(n, gender)} ({n}) {singular if n == 1 else plural}'


def genitive_name(name):
    """Προσεγγιστική γενική ονόματος (π.χ. Αλέξανδρος -> Αλεξάνδρου). Το κείμενο ελέγχεται από το HR."""
    if not name:
        return name
    words = []
    for word in name.split():
        low = word.lower()
        if low.endswith('ος'):
            word = word[:-2] + 'ου'
        elif low.endswith('ης'):
            word = word[:-1]
        elif low.endswith('ας'):
            word = word[:-1]
        elif low.endswith(('α', 'η', 'ά', 'ή')):
            word = word + 'ς'
        words.append(word)
    return ' '.join(words)


def _fmt_date(d):
    return d.strftime('%d.%m.%Y') if d else ''


def _fmt_days(days):
    """Ημέρες με ένα δεκαδικό (ελληνική υποδιαστολή), χωρίς αποκοπή."""
    return f'{days:.1f}'.replace('.', ',')


def _runs(numbers):
    """[25, 26, 27, 30, 31] -> «25-27 και 30-31»."""
    numbers = sorted(numbers)
    runs = []
    start = prev = numbers[0]
    for n in numbers[1:]:
        if n == prev + 1:
            prev = n
            continue
        runs.append((start, prev))
        start = prev = n
    runs.append((start, prev))
    texts = [str(a) if a == b else f'{a}-{b}' for a, b in runs]
    return ' και '.join(texts)


def overlapping(a, b):
    """Επικάλυψη με βάση τις ημέρες (κλειστά διαστήματα). Δεν χρησιμοποιείται το work_intervals.overlapping,
    που θεωρεί μη επικαλυπτόμενα δύο διαστήματα με ίδια ημερομηνία έναρξης."""
    return a.start <= b.end and b.start <= a.end


def _merge(intervals):
    """Ενώνει διαστήματα που επικαλύπτονται ή είναι διαδοχικές ημέρες."""
    merged = []
    for iv in sorted(intervals, key=lambda i: (i.start, i.end)):
        if merged and iv.start <= merged[-1][1] + timedelta(days=1):
            merged[-1][1] = max(merged[-1][1], iv.end)
        else:
            merged.append([iv.start, iv.end])
    return merged


def _covered(iv, merged):
    return any(start <= iv.start and iv.end <= end for start, end in merged)


def _subtract(iv, merged):
    """Τα τμήματα του διαστήματος iv που δεν καλύπτονται από τα (ενωμένα) διαστήματα merged."""
    pieces, start = [], iv.start
    for m_start, m_end in merged:
        if m_end < start or m_start > iv.end:
            continue
        if m_start > start:
            pieces.append((start, m_start - timedelta(days=1)))
        start = max(start, m_end + timedelta(days=1))
    if start <= iv.end:
        pieces.append((start, iv.end))
    return pieces


def _covered_note(a_numbers, b_numbers):
    if len(a_numbers) == 1:
        subject = f'Η από α/α {a_numbers[0]} προϋπηρεσία δεν αναγνωρίζεται, καθώς καλύπτεται'
    else:
        subject = f'Οι από α/α {_runs(a_numbers)} προϋπηρεσίες δεν αναγνωρίζονται, καθώς καλύπτονται'
    if len(b_numbers) == 1:
        obj = f'από την από α/α {b_numbers[0]} προϋπηρεσία πλήρους απασχόλησης'
    else:
        obj = f'από τις από α/α {_runs(b_numbers)} προϋπηρεσίες πλήρους απασχόλησης'
    return f'{subject} πλήρως {obj} του πίνακα των αναγνωριζόμενων προϋπηρεσιών.'


def _partial_note(a_numbers, b_numbers):
    if len(a_numbers) == 1:
        subject = f'η από α/α {a_numbers[0]} προϋπηρεσία αλληλοεπικαλύπτεται'
    else:
        subject = f'οι από α/α {_runs(a_numbers)} προϋπηρεσίες αλληλοεπικαλύπτονται'
    if len(b_numbers) == 1:
        obj = f'με την από α/α {b_numbers[0]} προς αναγνώριση προϋπηρεσία πλήρους απασχόλησης'
    else:
        obj = f'με τις από α/α {_runs(b_numbers)} προς αναγνώριση προϋπηρεσίες πλήρους απασχόλησης'
    return f'{subject} μερικώς {obj}.'


def _relation(app):
    lines = [app.get_type_display() or '']
    if app.get_work_type_display():
        lines.append(app.get_work_type_display())
    if app.day_percentage is not None and app.day_percentage < 1:
        lines.append(f'Ποσοστό απασχόλησης: {app.day_percentage:.0%}')
    return '\n'.join(line for line in lines if line)


def _row(number, app, start=None, end=None):
    return {
        'no': number,
        'organization': app.organization or '',
        'relation': _relation(app),
        'start': _fmt_date(start or app.start_date),
        'end': _fmt_date(end or app.end_date),
        'documents': (app.doc_descr() or '').strip(),
    }


def build_report_context(decision):
    employee = decision.employee
    cutoff = decision._hire_cutoff()
    apps = sorted(
        decision._applications_before_hire(decision.applications.all()),
        key=lambda a: (a.start_date, a.end_date, a.pk),
    )
    numbers = {app.pk: i for i, app in enumerate(apps, start=1)}
    intervals = {app.pk: app.to_interval(cutoff) for app in apps}

    # Πλήρης απασχόληση (ποσοστό ημέρας >= 100%). Αν μια πλήρης σύμβαση καλύπτεται ολόκληρη από άλλες
    # (μεγαλύτερες) πλήρους απασχόλησης, δεν αναγνωρίζεται (Πίνακας Α), αλλιώς ανήκει στον Πίνακα Β.
    full_all = [app for app in apps if (app.day_percentage or 0) >= 1]
    full, absorbed_full = [], []
    for app in sorted(full_all, key=lambda a: (-(a.end_date - a.start_date).days, a.start_date, a.pk)):
        if _covered(intervals[app.pk], _merge([intervals[k.pk] for k in full])):
            absorbed_full.append(app)
        else:
            full.append(app)
    full.sort(key=lambda a: numbers[a.pk])
    merged_full = _merge([intervals[app.pk] for app in full])

    table_a, partial_apps = list(absorbed_full), {}
    for app in apps:
        if app in full_all:
            continue
        iv = intervals[app.pk]
        if _covered(iv, merged_full):
            table_a.append(app)
            continue
        overlapped = tuple(b.pk for b in full if overlapping(iv, intervals[b.pk]))
        if overlapped:
            partial_apps.setdefault(overlapped, []).append(app.pk)
    table_a.sort(key=lambda a: numbers[a.pk])

    recognised = [app for app in apps if app not in table_a]
    # Στον πίνακα των αναγνωριζόμενων και στις παραγράφους επικάλυψης οι Α/Α είναι νέοι (χωρίς τον Πίνακα Α)
    rec_numbers = {app.pk: i for i, app in enumerate(recognised, start=1)}
    partial = {
        tuple(sorted(rec_numbers[pk] for pk in b_pks)): sorted(rec_numbers[pk] for pk in a_pks)
        for b_pks, a_pks in partial_apps.items()
    }

    table_a_notes = []
    by_cover = {}
    for i, app in enumerate(table_a, start=1):
        cover = tuple(sorted(rec_numbers[b.pk] for b in full if overlapping(intervals[app.pk], intervals[b.pk])))
        by_cover.setdefault(cover, []).append(i)
    for cover, a_numbers in sorted(by_cover.items(), key=lambda kv: min(kv[1])):
        table_a_notes.append(_covered_note(a_numbers, list(cover)))

    # Τελικά διαστήματα αναγνώρισης: το τέλος κόβεται στην ανάληψη καθηκόντων (to_interval) και τα μη πλήρους
    # απασχόλησης αφαιρούν τις ημέρες που καλύπτονται από πλήρη απασχόληση (η ημέρα μετράει έτσι κι αλλιώς μία φορά).
    final_pieces = {}
    for app in recognised:
        iv = intervals[app.pk]
        final_pieces[app.pk] = [(iv.start, iv.end)] if app in full_all else _subtract(iv, merged_full)

    # Ομάδες επικαλυπτόμενων συμβάσεων -> Πίνακας χρόνου. Ο χάρτης και οι ομάδες υπολογίζονται με όλες τις
    # συμβάσεις (και του Πίνακα Α, που καλύπτονται από πλήρη απασχόληση), ώστε το άθροισμα να συμφωνεί
    # με το Decision.calc (ο μήνας των 30 ημερών δεν είναι προσθετικός αν αφαιρεθούν διαστήματα).
    groups = []
    for app in apps:
        iv = intervals[app.pk]
        merged_group = [app]
        for g in [g for g in groups if any(overlapping(iv, intervals[o.pk]) for o in g)]:
            merged_group += g
            groups.remove(g)
        groups.append(merged_group)

    full_map, current_days = interval_map([intervals[app.pk] for app in apps])
    ref_date = decision._ymd_ref_date()
    time_rows = []
    group_no = 0
    for group in sorted(groups, key=lambda g: min(numbers[a.pk] for a in g)):
        shown = [a for a in sorted(group, key=lambda a: numbers[a.pk]) if a not in table_a]
        if not shown:
            continue
        group_no += 1
        group_rows = []
        group_ids = {a.pk for a in group}
        days = sum(el['days'] for el in full_map if set(el['idx']) & group_ids)
        years, months, rest = calc_ymd(days, ref_date)
        for app in shown:
            # ο χρόνος της ομάδας επαναλαμβάνεται σε κάθε γραμμή της, όπως στο πρακτικό του HR
            for start, end in final_pieces[app.pk]:
                row = _row(group_no, app, start, end)
                row.update({'years': years, 'months': months, 'days': _fmt_days(rest)})
                group_rows.append((start, end, row))
        time_rows += [row for _, _, row in sorted(group_rows, key=lambda r: (r[0], r[1]))]

    result = decision.calc()
    years, months, days = result['y_current'](), result['m_current'](), result['d_current']()
    prior_note = ''
    if result['prior_days'] >= 1:
        prior_y, prior_m, prior_d = calc_ymd(result['prior_days'], ref_date)
        prior_note = (
            f'Από τον ανωτέρω χρόνο έχει αφαιρεθεί χρόνος προηγούμενων αποφάσεων αναγνώρισης '
            f'({prior_y} έτη, {prior_m} μήνες, {int(prior_d)} ημέρες).'
        )

    info = employee.get_personal_info()
    rankclass = employee.rankclass_set.first()
    gender = info.gender
    given = info.given_name or ''
    surname = info.surname or ''
    article = {'F': 'της', 'M': 'του'}.get(gender, 'του/της')

    return {
        'doc_date': _fmt_date(decision.date) or EMPTY,
        'ref_no': decision.ref_no or EMPTY,
        'full_name': f'{given} {surname}'.strip(),
        'full_name_gen': genitive_name(f'{given} {surname}'.strip()),
        'fathers_name': info.fathers_name or EMPTY,
        'article': article,
        'article_nom': {'F': 'Η', 'M': 'Ο'}.get(gender, 'Ο/Η'),
        'own_gen': {'F': 'της', 'M': 'του'}.get(gender, 'του/της'),
        'fathers_name_gen': genitive_name(info.fathers_name) if info.fathers_name else EMPTY,
        'rank': (rankclass.rank if rankclass and rankclass.rank else EMPTY),
        'department': info.department.title_gr if info.department else EMPTY,
        'fek': EMPTY,
        'application_ref': EMPTY,
        'application_date': EMPTY,
        'from_date': EMPTY,
        'all_apps': [_row(numbers[app.pk], app) for app in apps],
        'has_table_a': bool(table_a),
        'table_a': [_row(i, app) for i, app in enumerate(table_a, start=1)],
        'table_a_notes': table_a_notes,
        'has_partial': bool(partial),
        'partial_notes': [_partial_note(a, list(b)) for b, a in sorted(partial.items(), key=lambda kv: min(kv[1]))],
        'recognised': [
            _row(rec_numbers[app.pk], app, start, end)
            for app in recognised for start, end in final_pieces[app.pk]
        ],
        'time_rows': time_rows,
        'total_years': years,
        'total_months': months,
        'total_days': days,
        'total_in_words': duration_in_words(years, months, days),
        'prior_note': prior_note,
        'notes': decision.notes or '',
    }


def render_report(decision):
    doc = DocxTemplate(str(TEMPLATE_PATH))
    doc.render(build_report_context(decision))
    out = io.BytesIO()
    doc.save(out)
    out.seek(0)
    return out
