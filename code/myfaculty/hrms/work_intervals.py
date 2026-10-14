from datetime import date, timedelta
#from hrms.utils import calc_days
import math
from hrms.utils import days_in_interval

# Check whether two intervals do not have overlap
def not_overlapping(int1, int2):
    s1 = int1.start
    s2 = int2.start
    e1 = int1.end
    e2 = int2.end

    if s1 < s2:
        return e1 < s2
    elif s1 > s2:
        return e2 < s1
    else:
        return True
    
def overlapping(int1, int2):
    return not not_overlapping(int1, int2)


class interval:
    
    def __init__(self, start, end, value=0, idx=0):
        self.start = start
        self.end = end
        self.value = value
        self.idx = idx
        
        
    def __str__(self):
        return f'({self.start.strftime("%d-%m-%Y")}, {self.end.strftime("%d-%m-%Y")}, val={self.value}, idx={self.idx})'
    
    def __repr__(self):
        return f'({self.start.strftime("%d-%m-%Y")}, {self.end.strftime("%d-%m-%Y")}, val={self.value}, idx={self.idx})'
    
    def __eq__(self, el):
        return ( self.start == el.start ) and (self.end == el.end )
    
    def __gt__(self, el):
        return self.start > el.end
    
    def __lt__(self, el):
        return el.start > self.end
    
    def overlaps_with(self, i):
        return overlapping(self, i)
    
    def does_not_overlap_with(self, i):
        return not_overlapping(self, i)
    
    def calendar_days(self):
        return days_in_interval(self.start, self.end)
    
    def trimmed(self, d_start = None, d_end = None):
        
        if d_start:
            start = max(d_start, self.start)
        else:
            start = self.start
        
        if d_end:
           end = min(d_end, self.end)
        else:
           end = self.end

        return interval(
            start, end, value=self.value, idx=self.idx
        )

    def is_in_year(self, year):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)   
        year_interval = interval(year_start, year_end)
        return self.overlaps_with(year_interval)
    
    def trimmed_in_year(self, year):
        if self.is_in_year(year):
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)   
            return self.trimmed(d_start = year_start, d_end = year_end )
        else:
            raise ValueError(f'Interval {self} is not in year {year}')
        

# def interval_map(intervals):
#     intervals = sorted(intervals, key=lambda s:s.start)
#     starts = [ {
#             'idx' : v.idx,
#             'date' : v.start,
#             'flag' : 'start',
#             'value' : v.value,
#         }
#         for i, v in enumerate(intervals) ]

#     ends = [ {
#             'idx' : v.idx,
#             'date' : v.end,
#             'flag' : 'end',
#             'value' : v.value,
#         }
#         for i, v in enumerate(intervals) ]

#     dates = sorted(starts + ends, key = lambda s: s['date'])
#     idxs = [ dates[0]['idx'] ]

#     map_el = {'date' : dates[0]['date'],
#             'value' : dates[0]['value'],
#             'idx' : idxs.copy() }

#     map_interval = [map_el]
#     for d in dates[1:]:
        
#         curr_date = d['date']
        
#         new_map_el = {}
#         if d['flag'] == 'end':
#             idxs.remove(d['idx'])
#             value = map_el['value'] - d['value']
#             new_map_el['date'] = curr_date 

#         elif d['flag'] == 'start':
#             idxs.append(d['idx'])
#             value = map_el['value'] + d['value']
#             new_map_el['date'] = curr_date 

#         new_map_el['value'] = value
#         new_map_el['idx'] = idxs.copy()
        
#         map_interval.append(new_map_el)
#         map_el = new_map_el

#     total_days = 0

#     non_zero_map = []
#     for i, v in enumerate(map_interval):
#         if i < len(map_interval) - 1:

#             # Next date
#             nv = map_interval[ i + 1 ]
            
#             start = v['date']
#             end = nv['date']
#             if i < len(map_interval) - 2:
#                 end = nv['date'] - timedelta(days = 1)

#             if start <= end:
                
#                 calendar_days = calc_days(start, end)
#                 if v['value'] > 1:
#                         v['value'] = 1.0
                
#                 days = v['value'] * calendar_days
                    
#                 if days > 0:
                        
#                     total_days += days
#                     v['start'] = v['date']
#                     v['end'] = end
#                     v['calendar_days'] = calendar_days
#                     v['days'] = days
#                     v['cumulative_days'] = total_days
#                     non_zero_map.append(v)

            
#     return non_zero_map, total_days

def interval_map(intervals):

    # No intervals (e.g. a year without applications): nothing to count
    if not intervals:
        return [], 0

    # Pick out the start dates and sort them, remembering the index and values of each interval
    starts = [ {
            'idx' : v.idx,
            'date' : v.start,
            'value' : v.value,
        }
        for i, v in enumerate(intervals) ]

    starts = sorted(starts, key=lambda s:s['date'])

    # Pick out the end dates and sort them, remembering the index and values of each interval
    ends = [ {
            'idx' : v.idx,
            'date' : v.end,
            'value' : v.value,
        }
        for i, v in enumerate(intervals) ]

    ends = sorted(ends, key=lambda s:s['date'])

    # First date is the first start date
    curr_date = starts[0]['date']

    # Final date (largest end_date)
    final_date = ends[-1]['date']    

    # List of indices first contains the index of the first interval. Value is originally the value of the first interval
    idxs = [ starts[0]['idx'] ]
    value = starts[0]['value']

    # List of dictionaries first contains the info of the first interval    
    map_el = {
        'date' : curr_date,
        'value' : value,
        'idx' : idxs.copy()                
    }    
    map_interval = [map_el]

    # the first start date must be popped out of the start date list
    starts.pop(0) 

    total_days = 0
    while len(ends) > 0:
        
        # get the next start date and end date 
        start_date = starts[0]['date'] if len(starts) > 0 else None

        # there should always be an end date
        end_date = ends[0]['date'] 
        if start_date:

            # Smallest start date means a new interval starts
            if start_date <= end_date:

                # Update indices and value
                idx = starts[0]['idx']
                new_value = starts[0]['value']
                # print('Found start:', start_date, new_value)
                idxs.append( idx )
                # print('Old value=', value)
                value += new_value
                # print('value=', value)
                # remove the start date from the list of start dates
                starts.pop(0)
                curr_date = start_date

                went_up = True

            # Smallest end date means an old interval ends            
            else:
                # Update indices and value                            
                idx = ends[0]['idx']
                new_value = ends[0]['value']
                # print('Found end:', end_date, new_value)
                
                idxs.remove( idx )
                # print('Old value=', value)
                value = value - new_value
                # print('value=', value)

                # remove the start date from the list of start dates
                ends.pop(0)
                curr_date = end_date

                went_up = False

        # The last end date
        else:
            # Update indices and value                            
            idx = ends[0]['idx']
            new_value = ends[0]['value']
            # print('Found end:', end_date, new_value)
            idxs.remove( idx )
            # print('Old value=', value)
                        
            value = value - new_value
            # print('value=', value)
            # remove the start date from the list of start dates
            ends.pop(0)
            curr_date = end_date

            went_up = False


        # Check if map already contains intervals
        if len(map_interval) > 0:

            # Get previous interval
            previous_el = map_interval[-1]

            # Previous interval ends a day before the current interval
            if went_up:
                previous_el['end'] = curr_date - timedelta(days = 1)
            else:
                previous_el['end'] = curr_date

            previous_el['start'] = previous_el['date']            
            calendar_days = days_in_interval(previous_el['start'], previous_el['end'])
            previous_el['calendar_days'] = calendar_days
            value_thr = previous_el['value'] if previous_el['value'] <=1 else 1.0
            previous_el['days'] = value_thr * previous_el['calendar_days']
            total_days += previous_el['days']

        if went_up:
            date_to_set = curr_date
        else:
            date_to_set = curr_date + timedelta(days = 1)

        map_interval.append({
                'date' : date_to_set,
                'value' : value,
                'idx' : idxs.copy()                
            })

    # Last emelement ends at date end_date

    # last = map_interval[-1]
    # last['end'] = final_date
    # last['start'] = last['date']
    # calendar_days = (previous_el['end'] - previous_el['start']).days + 1
    # last['calendar_days'] = calendar_days
    # last['days'] = last['value'] * last['calendar_days']
    # total_days += last['days']

    map_interval.pop(-1)
    # Remove zero elements
    map_interval = [s for s in map_interval if s['days'] > 0]
    
    return map_interval, total_days
