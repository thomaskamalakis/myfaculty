import os
import sys
import django
from datetime import date
import csv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myfaculty.settings")
django.setup()

from hrms.models import Decision, Application

decision = Decision.objects.first()

apps = Application.objects.all()
days_dict = decision.calc_by_year()
s = 0
for k, v in days_dict.items():
    s+= v
    print(k, '%6.2f'%v)
print(s)



with open("years.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["year", "days"])  # header

    for key, value in days_dict.items():
        writer.writerow([key, value])