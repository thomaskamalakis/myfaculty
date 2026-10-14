from django.http import HttpResponse, FileResponse, Http404
from phdstuds.models import Recommendation
import csv

def recommendation_dicts(objs):
    data = []
    for obj in objs:
        try:
            d = {
                'subject': obj.thesis.subject_gr,
                'supevisor_surname': obj.thesis.supervisor.surname,
                'supevisor_given_name': obj.thesis.supervisor.given_name,
                'candidate_surname': obj.thesis.candidate.surname,
                'candidate_given_name': obj.thesis.candidate.given_name,
                'year' : obj.year,
                'notes' : obj.notes,
                'recommendation' : obj.get_recommendation_display()
            } 
            data.append(d)
        except AttributeError:
            pass

    return data 

    
def recommendation_csv_response(objs):
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'},
    )

    writer = csv.writer(response, delimiter=';', quoting = csv.QUOTE_ALL)        
    i = 0
    for obj in objs:
        try:
            d = {
                'subject': obj.thesis.subject_gr,
                'supevisor_surname': obj.thesis.supervisor.surname,
                'supevisor_given_name': obj.thesis.supervisor.given_name,
                'candidate_surname': obj.thesis.candidate.surname,
                'candidate_given_name': obj.thesis.candidate.given_name,
                'year' : obj.year,
                'notes' : obj.notes,
                'recommendation' : obj.recommendation
            }            
            if i==0:
                writer.writerow(d.keys())
            l = [d[k] for k in d.keys()]
            i += 1
            writer.writerow(l)
        except AttributeError as e:
            pass

    return response
