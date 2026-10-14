from datetime import date, timedelta
from hrms.utils import calc_days
import math

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
        return (self.end-self.start).days + 1
    
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
                idxs.append( idx )
                value += new_value

                # remove the start date from the list of start dates
                starts.pop(0)
                curr_date = start_date

            # Smallest end date means an old interval ends            
            else:
                # Update indices and value                            
                idx = ends[0]['idx']
                new_value = ends[0]['value']
                idxs.remove( idx )
                value -= new_value

                # remove the start date from the list of start dates
                ends.pop(0)
                curr_date = end_date

        # The last end date
        else:
            # Update indices and value                            
            idx = ends[0]['idx']
            new_value = ends[0]['value']
            idxs.remove( idx )
            value -= new_value

            # remove the start date from the list of start dates
            ends.pop(0)
            curr_date = end_date

        map_interval.append({
                'date' : curr_date,
                'value' : value,
                'idx' : idxs.copy()                
            })

    # Now we do the calculations for the total number of days calculated by the intervals
    total_days = 0
    aug_map = []

    for i, curr_el in enumerate(map_interval):

        # For every element of the map interval except the last one        
        if i < len(map_interval) - 1:

            # take the next element
            next_el = map_interval[ i + 1 ]
            
            start_date = curr_el['date']

            # The end date of the interval should be one day before the next date UNLESS there is a single contract left!!!
            idxs = curr_el['idx']
            if len(idxs) > 1:
                end_date = next_el['date'] - timedelta(days=1)
            else:
                end_date = next_el['date']
            
            # Caution: need to think about this! check if the start_date is not larger than the end_date. I think this implies 
            if start_date < end_date:

                # Value needs a 100% cutoff
                value = curr_el['value'] if curr_el['value'] <=1.0 else 1.0

                # Calculate calendar days. 
                calendar_days = (end_date-start_date).days + 1
                days = value * calendar_days
                total_days += days

                new_el = {
                    'start' : start_date,
                    'end' : end_date,
                    'calendar_days' : calendar_days,
                    'days' : days,
                    'cumulative_days' : total_days,
                    'value' : value,
                    'date' : curr_el['date']
                }       
                aug_map.append(new_el)
           
    return aug_map, total_days
