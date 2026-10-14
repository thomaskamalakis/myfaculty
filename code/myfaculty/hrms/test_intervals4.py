import os
import sys
import django
from datetime import date
import csv
from work_intervals import interval, interval_map

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myfaculty.settings")
django.setup()

from hrms.models import Decision, Application

d1s = date(2005,6,1)
d1e = date(2006,9,12)
d2s = date(2006,7,1)
d2e = date(2006,7,1)

intervals = [
    interval(d1s, d1e, 1.0, 1),
    interval(d2s, d2e, 1.25, 2)
]
year = 2006
t_intervals = [s.trimmed_in_year(year) for s in intervals]

m, t = interval_map(intervals)
for s in m:
    print(f'{s['start']} ---> {s['end']} {s['calendar_days']}x{s['value']}={s['days']}')
print(t)

m1, t1 = interval_map(t_intervals)

for s in m1:
    print(f'{s['start']} ---> {s['end']} {s['calendar_days']}x{s['value']}={s['days']}')
print(t1)
