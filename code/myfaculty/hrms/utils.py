import math
from django.utils import timezone
from datetime import date, timedelta
from calendar import monthrange
from dateutil.relativedelta import relativedelta
from django.conf import settings

YEAR_DAYS = 360
MONTH_DAYS = 30
# Create your models here.

##############################################
# Helper Functions
##############################################
    
def split_date(d):
    return d.year, d.month, d.day

def calc_days(date1, date2):
    if date2 < date1:
        date1, date2 = date2, date1

    delta = date2 - date1
    return delta.days + 1

def _calc_method():
    return getattr(settings, 'CALC_WE_METHOD', '30 day month')

# Day number on a 30/360 calendar
def day_number_30(d):
    return 360 * d.year + 30 * d.month + d.day

# Number of days of the interval [start, end] (both ends included).
# '30 day month': a full calendar month counts 30 days, a partial month its actual days.
# 'strict calendar': actual calendar days.
def days_in_interval(start, end):
    if _calc_method() == '30 day month':
        return day_number_30(end + timedelta(days=1)) - day_number_30(start)
    return (end - start).days + 1

# Split a number of days into years, months, days.
# '30 day month': 360 day year, 30 day month.
# 'strict calendar': actual years (365/366 days) counted from ref_date, 30 day month.
def calc_ymd(days, ref_date=None):
    if _calc_method() == '30 day month':
        year_days = YEAR_DAYS
        years = math.floor(days/year_days)
        days -= years*year_days
    else:
        years = 0
        while True:
            if ref_date:
                start = ref_date + relativedelta(years=years)
                year_days = (start + relativedelta(years=1) - start).days
            else:
                year_days = 365
            if days < year_days:
                break
            days -= year_days
            years += 1
    months = math.floor(days/MONTH_DAYS)
    days -= months*MONTH_DAYS
    return years, months, days


# Difference according to 30 day month and 360 day year
def date_diff_30(date1, date2):
    if date1 > date2:
        date2, date1 = date1, date2
    
    y1, m1, d1 = split_date(date1)
    y2, m2, d2 = split_date(date2)
    
    Dy = y2-y1
    Dm = m2-m1

    if Dm < 0:
        Dy -= 1
        Dm += 12
    
    Dd = d2-d1
    if Dd < 0:
        Dd += 30
        Dm -= 1
    
    if Dm < 0:
        Dy -= 1
        Dm += 12
    
    return Dy, Dm, Dd
    

def calc_ymd_to_days(y,m,d):
    return y * YEAR_DAYS + m * MONTH_DAYS + d

def calc_experience(date1, date2):
    # Swap dates if reverse
    if date1 > date2:
        date2, date1 = date1, date2

    # Get year, month and date from every date
    y1, m1, d1 = split_date(date1)
    y2, m2, d2 = split_date(date2)

    years = y2 - y1
    months = m2 - m1

    # If months are negative we must subtract 1 from years and add 12 to months
    if months < 0:
        years -= 1
        months += 12
    
    # calculate days, assuming each month is thirty days
    days = d2 - d1
    
    # If days are negative, subtract one month
    if days<0:
        days += MONTH_DAYS
        month -= 1
    
    # Check for negative months as previously
    if months < 0:
        years -= 1
        months += 12

    return years, months, days

def add_experience(y1,m1,d1,y2,m2,d2):
    total_days = (y1 * YEAR_DAYS + m1 * MONTH_DAYS + d1) + (y2 * YEAR_DAYS + m2 * MONTH_DAYS + d2)
    years = math.floor(total_days/YEAR_DAYS)
    remainder = math.remainder(total_days, YEAR_DAYS)
    months = math.floor(remainder/MONTH_DAYS)
    days = math.remainder(remainder, MONTH_DAYS)
    return years, months, days    

def calc_work_exp(employee):
    from .models import Reference, Interval

    we_ref = Reference.objects.get(employee = employee) 
    today = timezone.now().date()        
    
    # Estimate number of days from the approved applications
    no_days_app_total = Interval.objects.calc_days_for_employee(employee)
    years_app, months_app, days_app = calc_ymd(no_days_app_total)

    # Estimate number of days from previous reference point
    no_days_prior_total = we_ref.no_days
    years_prior, months_prior, days_prior = calc_ymd(no_days_prior_total)

    # Estimate total number of days for work experience (including applications and reference point)

    no_days_we = no_days_app_total + no_days_prior_total
    years_we, months_we, days_we = calc_ymd(no_days_we)

    return {
        'employee' : employee,
        'total_app_days' : no_days_app_total,
        'total_prior_days' : no_days_prior_total,        
        'today' : today,
        'app_years' : years_app,
        'app_months' : months_app,
        'app_days' : days_app,
        'prior_years' : years_prior,
        'prior_months' : months_prior,
        'prior_days' : days_prior,
        'we_years' : years_we,
        'we_months' : months_we,
        'we_days' : days_we
    }

def get_context_from_rows(rows, px_per_day = 4, label_width = 250):

    min_date = None
    max_date = None

    all_items = []
    for row in rows:
        all_items += row['items']

    for item in all_items:

        if not max_date:
            max_date = item['end']
        elif max_date < item['end']:
            max_date = item['end']

        if not min_date:
            min_date = item['start']
        elif min_date > item['start']:
            min_date = item['start']

    # Χωρίς διαστήματα (π.χ. απόφαση χωρίς συμβάσεις) δεν υπάρχει χρονοδιάγραμμα
    if not all_items:
        return {
            'rows' : rows,
            'months' : [],
            'timeline_width' : 0,
            'full_timeline_width' : label_width
        }

    min_date = date(min_date.year, min_date.month, 1)
    last_day = monthrange(max_date.year, max_date.month)[1]
    max_date = date(max_date.year, max_date.month, last_day)

    year = min_date.year
    month = min_date.month

    months = []

    while date(year,month,1) < date(max_date.year, max_date.month, 1):
        no_days = monthrange(year, month)[1]
        months.append({
            'label' : date(year,month,1).strftime("%m/%Y"),
            'width' : no_days * px_per_day
        })

        month += 1

        if month > 12:
            month = 1
            year += 1
    
    for item in all_items:
        item['left'] = (item['start'] - min_date).days * px_per_day
        item['width'] = ( (item['end'] - item['start']).days + 1 ) * px_per_day

    timeline_width = sum(m['width'] for m in months)
    full_timeline_width = timeline_width + label_width

    return {
        'rows' : rows,
        'months' : months,
        'timeline_width' : timeline_width,
        'full_timeline_width' : full_timeline_width
    }

def decision_apps_to_context(decision, px_per_day = 2, label_width = 250):
    rows = []

    for app in decision.applications.all():
        rows.append( 
            {
              'name' : app.display_name(),
              'items' : [
                  {
                      'title' : f'{app.day_percentage:.2%}',
                      'start' : app.start_date,
                      'end' : app.end_date,
                      'css_class' : 'bg-primary',
                  }
              ]
            }
        )
    return get_context_from_rows(rows, px_per_day=px_per_day, label_width=label_width)

def decision_map_to_context(map, px_per_day = 2, label_width = 250):
    
    rows = []
    for i, el in enumerate( map ):
        rows.append( 
            {
              'name' : f'{i}',
              'items' : [
                  {
                      'title' : f'{math.floor(el['days'])}ημ. ({el['value']:.2%})',
                      'start' : el['date'],
                      'end' : el['end'],
                      'css_class' : 'bg-success',
                  }
              ]
            }
        )
    return get_context_from_rows(rows, px_per_day=px_per_day, label_width=label_width)
    
        
    


        

        
