"""
Read-only computed endpoints for the hrms data, exposed as
GET .../<app>/<model>/<pk>/<name>/ on the HR and admin routers:

    myprofile/employee/<pk>/summary/      overview of one employee
    hrms/decision/<pk>/experience/        prior-service calculation of one decision

They give an API client (e.g. an LLM) the figures the HR UI shows, instead of
making it recompute them from raw rows. Each function takes (request, instance)
and returns a JSON-serialisable dict.
"""
from collections import Counter

from django.conf import settings
from django.utils import timezone

from hrms import models as hm
from myprofile.models import Employee


def _safe(function, *args):
    """Values derived from incomplete data (no reference date, no total_days ...)
    must not make the whole response fail."""
    try:
        return function(*args)
    except Exception:
        return None


def _labelled_counts(queryset, field, choices):
    labels = {code: str(label) for code, label in choices}
    counts = Counter(queryset.values_list(field, flat=True))
    return {labels.get(code, str(code)): n for code, n in counts.items()}


def employee_summary(request, employee):
    today = timezone.now().date()
    applications = hm.Application.objects.filter(employee=employee)
    decisions = hm.Decision.objects.filter(employee=employee).order_by('-date')
    payroll = hm.PayrollDecision.objects.filter(employee=employee)
    wage = hm.WageClass.objects.filter(employee=employee).first()
    rank = hm.RankClass.objects.filter(employee=employee).first()

    return {
        'employee': {
            'id': employee.pk,
            'display': str(employee),
            'type': str(employee.employee_type()),
            'date_hired': employee.date_hired,
            'wage_step_years': employee.wage_step_years,
        },
        'as_of': today,
        'wage_class': _safe(wage.info, today) if wage else None,
        'rank_class': _safe(rank.info, today) if rank else None,
        'applications': {
            'total': applications.count(),
            'by_type': _labelled_counts(applications, 'type', hm.Application.TYPE_CHOICES),
            'by_status': _labelled_counts(applications, 'status', hm.Application.STATUS_CHOICES),
        },
        # total_days / we_as_str are the values stored the last time the decision was calculated
        'decisions': [
            {
                'id': d.pk, 'date': d.date, 'ref_no': d.ref_no, 'total_days': d.total_days,
                'experience': _safe(d.we_as_str) if d.total_days is not None else None,
                'applications': d.applications.count(),
            }
            for d in decisions
        ],
        'payroll_decisions': {
            'total': payroll.count(),
            'by_type': _labelled_counts(payroll, 'decision_type', hm.PayrollDecision.DECISION_TYPE_CHOICES),
        },
    }


def decision_experience(request, decision):
    """Recalculates the decision (like the UI's calculation page: this refreshes
    and saves its stored total_days) and returns the breakdown."""
    result = decision.calc()
    entire_map = result['entire_map']

    # entire_map: consecutive segments {'date': start, 'value': sum of percentages, 'idx': application ids};
    # a segment lasts until the date of the next one. More than one id = overlapping contracts.
    overlaps = [
        {
            'from': segment['date'],
            'to': entire_map[i + 1]['date'],
            'application_ids': segment['idx'],
            'sum_of_percentages': segment['value'],
        }
        for i, segment in enumerate(entire_map[:-1])
        if len(segment['idx']) > 1
    ]

    return {
        'decision': {'id': decision.pk, 'display': str(decision), 'date': decision.date, 'ref_no': decision.ref_no},
        'calc_we_method': getattr(settings, 'CALC_WE_METHOD', '30 day month'),
        'total_days': result['total_days'],
        'prior_days': result['prior_days'],
        'all_days': result['all_days'],
        # Experience recognised by this decision alone, from earlier decisions, and in total
        'current': {'years': decision.years(), 'months': decision.months(), 'days': decision.days()},
        'prior': {'years': result['y_prior'], 'months': result['m_prior'], 'days': result['d_prior']},
        'all': {'years': result['y_all'], 'months': result['m_all'], 'days': result['d_all']},
        'by_year': {str(year): days for year, days in decision.calc_by_year().items()},
        'overlaps': overlaps,
        'applications': [
            {
                'id': app.pk, 'organization': app.organization, 'type': app.get_type_display(),
                'start_date': app.start_date, 'end_date': app.end_date, 'day_percentage': app.day_percentage,
            }
            for app in result['apps'].values()
        ],
    }


ACTIONS = {
    Employee: {'summary': employee_summary},
    hm.Decision: {'experience': decision_experience},
}
