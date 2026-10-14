from work_intervals import interval
from datetime import date
from work_intervals import interval_map
from datetime import datetime

APP_DATA = [
    {
        'start' : date(2004,2,1),
        'end' : date(2005,10,2),
        'day_percentage' : 0.7,
    },
    {
        'start' : date(2006,8,2),
        'end' : date(2007,4,10),
        'day_percentage' : 0.7,
    },
    {
        'start' : date(2007,1,1),
        'end' : date(2008,12,12),
        'day_percentage' : 0.5,
    },
    {
        'start' : date(2006,1,1),
        'end' : date(2007,2,10),
        'day_percentage' : 0.3,
    }
]

intervals = []
for i, v in enumerate(APP_DATA):
    new_i = interval(
        start=v['start'],
        end=v['end'],
        value=v['day_percentage'],
        idx = i
    )
    intervals.append(new_i)

t1 = datetime.now()
int_map, total_days = interval_map(intervals)
t2 = datetime.now()
print( (t2-t1).microseconds )
for v in int_map:
    print(v) 

