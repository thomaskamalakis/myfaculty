from django.db import models
from myprofile.models import Employee
from myprofile.directories import hrms_dir, hrms_payroll_decision_dir
from django.utils.translation import gettext_lazy as _
from hrms.work_intervals import interval, interval_map
from hrms.utils import calc_ymd_to_days, calc_days, calc_ymd, date_diff_30, days_in_interval
import math
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from django.conf import settings
from datetime import date
from copy import copy

HOURLY_WAGE = settings.HOURLY_WAGE 

class WageClass(models.Model):
    ref_date = models.DateField(null=True)
    employee = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL)
    ref_value = models.PositiveIntegerField(null=True, default=1)

    # Estimate when the wage class will change again
    def info(self, at = None):

        # Estimate how many years there have been between today and the reference year
        if not at:
            at = timezone.now().date()

        # No reference date yet (e.g. Employee/WageClass created without one) -
        # nothing can be computed, so return an all-None dict instead of
        # crashing on relativedelta(at, None).
        if not self.ref_date:
            return {key: None for key in (
                'at', 'ref_date', 'ref_value', 'curr_c', 'curr_d', 'next_c', 'next_d',
                'total_days_in', 'total_days_left',
                'y_in', 'm_in', 'd_in', 'y_left', 'm_left', 'd_left',
            )}

        # Έτη ανά κλιμάκιο για αυτόν τον εργαζόμενο (συνήθως 2, μερικές
        # κατηγορίες 3) - αν δεν υπάρχει employee, 2 σαν ασφαλές default.
        years_step = self.employee.wage_step_years if self.employee else 2

        def step_duration(step):
            # Μοναδική εξαίρεση στον κανόνα: η μετάβαση ΜΚ0->ΜΚ1 παίρνει
            # πάντα 1 έτος, ανεξαρτήτως wage_step_years - κάθε επόμενο
            # βήμα (1->2, 2->3, ...) παίρνει wage_step_years έτη.
            return 1 if step == 0 else years_step

        # Περπατάμε βήμα-βήμα από το ref_value/ref_date μέχρι να βρούμε το
        # τρέχον κλιμάκιο - δεν είναι πια απλή διαίρεση αφού τα βήματα δεν
        # έχουν όλα την ίδια διάρκεια (βλ. step_duration).
        curr_c, curr_d = self.ref_value, self.ref_date
        while True:
            step_end = curr_d + relativedelta(years=step_duration(curr_c))
            if step_end > at:
                break
            curr_c, curr_d = curr_c + 1, step_end

        # Next class: the current class + 1
        next_c = curr_c + 1

        # Date where the class will change next
        next_d = curr_d + relativedelta(years=step_duration(curr_c))

        # Total days in the current class
        total_days_in = (at-curr_d).days
        total_days_left = (next_d - at).days

        # Years, months, days format
        y_in, m_in, d_in = date_diff_30(curr_d, at)
        y_left, m_left, d_left = date_diff_30(next_d, at)

        return {
            'at' : at,
            'ref_date' : self.ref_date,
            'ref_value' : self.ref_value,
            'curr_c' : curr_c,
            'curr_d' : curr_d,
            'next_c' : next_c,
            'next_d' : next_d,
            'total_days_in' : total_days_in,
            'total_days_left' : total_days_left,
            'y_in' : y_in,
            'm_in' : m_in,
            'd_in' : d_in,
            'y_left' : y_left,
            'm_left' : m_left,
            'd_left' : d_left,
        }


# Τρέχουσα ακαδημαϊκή βαθμίδα (ΔΕΠ) ή διοικητικός βαθμός (διοικητικό
# προσωπικό) - ένα μοντέλο και για τα δύο, όπως και το PayrollDecision.rank
# που τροφοδοτεί τις τιμές του. Σε αντίθεση με το WageClass, δεν υπάρχει
# "επόμενη βαθμίδα/βαθμός" να προβλεφθεί (δεν αλλάζει αυτόματα με τον
# χρόνο) - μόνο πόσος καιρός έχει περάσει στην τρέχουσα.
class RankClass(models.Model):
    ref_date = models.DateField(null=True)
    employee = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL)
    rank = models.CharField(max_length=100, null=True, blank=True)

    def info(self, at=None):
        if not at:
            at = timezone.now().date()

        if not self.ref_date:
            return {key: None for key in ('at', 'ref_date', 'rank', 'total_days_in', 'y_in', 'm_in', 'd_in')}

        total_days_in = (at - self.ref_date).days
        y_in, m_in, d_in = date_diff_30(self.ref_date, at)

        return {
            'at': at,
            'ref_date': self.ref_date,
            'rank': self.rank,
            'total_days_in': total_days_in,
            'y_in': y_in,
            'm_in': m_in,
            'd_in': d_in,
        }


# Initial data for work experience of employees
class Reference(models.Model):
    ref_date = models.DateField(null=True)
    no_days = models.PositiveIntegerField(default=0)
    employee = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL)

    def set_from_ymd(self, years, months, days):
        self.no_days = calc_ymd_to_days(years, months, days)
            

# Work Experience Applications by employees
class Application(models.Model):    
    PENDING = "P"
    APPROVED = "A"
    REJECTED = "R"

    STATUS_CHOICES = (
        (PENDING, _("Εκκρεμεί")),
        (APPROVED, _("Εγκρίθηκε")),
        (REJECTED, _("Δεν εγκρίθηκε")),
    )

    FULLTIME = 'Fulltime'
    WORKCONTRACT = 'Workcontract'
    TEACHING407_FRACTION = 'Teaching407fractioonal'
    TEACHING_HOURS = 'Teachinghourly'
    TEACHING_DAYS = 'Teachingdays'  
    OTHER = 'OT'
    EXTERNAL = 'External'

    RESEARCH  = 'Research'
    TEACHING = 'Teaching'  
    
    TYPE_CHOICES = (
        (FULLTIME, _("Πλήρους Απασχόλησης")),
        (WORKCONTRACT, _("Σύμβαση Έργου")),
        (TEACHING407_FRACTION, _("Διδασκαλία με ανάθεση συμφ. με το 407/80 με έκτα")),
        (TEACHING_HOURS, _("Διδασκαλία (υπολογισμός με ώρες διδασκαλίας)")),
        (TEACHING_DAYS, _("Διδασκαλία (υπολογισμός με ημέρες διδασκαλίας)")),                
        (OTHER, _("Άλλος Τύπος")),        
        (EXTERNAL, _("Εμπειρία Εξωτερικού")),
    )

    WORK_CHOICES = (
        (TEACHING, _("Διδακτικό") ),
        (RESEARCH, _("Ερευνητικό") ),
        
    )

    date_submitted = models.DateField(null=True, blank=True)
    date_approved = models.DateField(null=True, blank=True)
    start_date = models.DateField(null=True)
    end_date = models.DateField(null=True)
    related_document1 = models.FileField(upload_to = hrms_dir, blank=True, null=True, help_text=_('To αρχείο της σύμβασης'))
    related_document2 = models.FileField(upload_to = hrms_dir, blank=True, null=True, help_text=_('Το αρχείο της βεβαίωσης') )
    related_desc = models.TextField(null=True, blank=True)
    employee = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL)
    payment = models.FloatField(null=True, blank=True)
    organization = models.CharField(null=True, max_length=255)
    notes = models.TextField(null=True, blank=True)
    notes_decision = models.TextField(null=True, blank=True)
    
    contract_id = models.CharField(null=True, blank=True, max_length=255)  
    document2_id = models.CharField(null=True, blank=True, max_length=255)  

    status = models.CharField(max_length=200, choices=STATUS_CHOICES, null=True)
    type = models.CharField(max_length=200, choices=TYPE_CHOICES, null=True)
    work_type = models.CharField(max_length=200, choices=WORK_CHOICES, null=True)
    day_percentage = models.FloatField(null=True, blank=True)
    assignment_percentage = models.PositiveIntegerField(null=True, blank=True)
    no_days = models.PositiveIntegerField(null=True, blank=True)
    no_hours = models.PositiveIntegerField(null=True, blank=True)
    ref_hours = models.PositiveIntegerField(null=True, blank=True, default=16)
    
    
    def to_dict(self):
        return {
            'date_submitted' : self.date_submitted,
            'start_date' : self.start_date,
            'end_date' : self.end_date,
            'organization' : self.organization,
            'notes' : self.notes,
            'notes_decision' : self.notes_decision,
            'status' : self.get_status_display(),
            'type' : self.get_type_display(),
            'work_type' : self.get_work_type_display(),
            'no_hours' : self.no_hours,
            'ref_hours' : self.ref_hours,
            'no_days' : self.no_days,
            'doc_descr' : self.doc_descr(),
            'payment' : self.payment
        }
    
    def doc_descr(self):
        contract_desc = ''
        document_desc = ''

        if self.contract_id:
            contract_desc = f'-Η σύμβαση με αριθμό {self.contract_id}\n'
            
        if self.document2_id:
            document_desc = f'-Η βεβαίωση με αριθμό {self.document2_id}\n'

        desc = contract_desc + document_desc

        if self.related_desc:
            desc = desc + '\n' + self.related_desc

        return desc
    
    def calc_day_percentage(self):
        calendar_days = days_in_interval(self.start_date, self.end_date)

        if self.type == Application.FULLTIME:
            self.day_percentage = 1.0
        
        elif self.type == Application.WORKCONTRACT:            
            self.day_percentage = self.payment / HOURLY_WAGE / 8 / 25 * 30 / calendar_days
        
        elif self.type == Application.TEACHING407_FRACTION:
            self.day_percentage = self.assignment_percentage/6

        elif self.type == Application.TEACHING_DAYS:
            self.day_percentage = self.no_days / calendar_days

        elif self.type == Application.TEACHING_HOURS:
            # weeks6 = calendar_days / 6
            # weeks_employed = weeks6 * self.no_hours / 16
            # days_employed = weeks_employed * 6
            days_employed = calendar_days * self.no_hours / self.ref_hours
            self.day_percentage = days_employed / calendar_days

        # OTHER και EXTERNAL: το day_percentage το δίνει ο χρήστης (π.χ. από βεβαίωση) - δεν ξαναυπολογίζεται.
                
    def day_percentage_formatted(self):
        return f'{self.day_percentage:.2%}'

    def __str__(self):
        if self.contract_id:
            text_contract = f' αρ. σύμβασης: {self.contract_id}'
        else:
            text_contract = ''

        if self.document2_id:
            text_doc= f' αρ. βεβαίωσης: {self.document2_id}'
        else:
            text_doc = ''
            
        return f'Σύμβαση από {self.start_date} εώς {self.end_date} στον οργανισμό {self.organization} {text_doc} {text_contract}'
    
    def display_name(self):
        return f'{self.start_date}->{self.end_date} - {self.organization[:15]}'
    
    def save(self, *args, **kwargs):
        self.calc_day_percentage()
        if not self.pk:
            self.date_submitted = timezone.now().date()
        super().save(*args, **kwargs)

    def to_interval(self, cutoff_date = None):

        return interval(
            start = self.start_date,
            end = self.end_date,
            value = self.day_percentage,
            idx = self.pk
        )
    
    def is_in_year(self, year):
        return self.to_interval().is_in_year(year)
    
class Decision(models.Model):

    employee = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL)
    applications = models.ManyToManyField(Application, related_name = 'decisions')
    date = models.DateField(null=True)
    total_days = models.FloatField(null=True, blank=True)
    ref_no = models.CharField(null=True, max_length=255)
    notes = models.TextField(null=True, blank=True)
    document = models.FileField(upload_to = hrms_dir, null=True, help_text=_('Απόφαση'), blank=True )
    
    def _ymd_ref_date(self):
       # Αρχή μέτρησης για πραγματικά έτη (μόνο στο 'strict calendar')
       return self.employee.date_hired or self.date

    def years(self):
       y, __, ___ = calc_ymd( self.total_days, self._ymd_ref_date() )
       return y
    
    def months(self):
       __, m, ___ = calc_ymd( self.total_days, self._ymd_ref_date() )
       return m
    
    def days(self):
       __, __ , d = calc_ymd( self.total_days, self._ymd_ref_date() )
       return math.floor(d)
    
    def __str__(self):
        return f'{self.employee}, date: {self.date}'
    
    @staticmethod
    def affected_by(applications):
        """Οι αποφάσεις που περιέχουν τις συμβάσεις. Πρέπει να κληθεί ΠΡΙΝ τη διαγραφή τους, γιατί μετά
        η σχέση M2M έχει χαθεί. Επιστρέφει λίστα (όχι lazy queryset) για να μη χαθεί και αυτή."""
        return list(Decision.objects.filter(applications__in=applications).distinct())

    @staticmethod
    def recalc_many(decisions):
        """Επανυπολογίζει το total_days των αποφάσεων και όσων μεταγενέστερων του ίδιου εργαζομένου
        τις μετράνε ως προηγούμενες. Αποφάσεις χωρίς ημερομηνία παραλείπονται."""
        earliest = {}
        for decision in decisions:
            if decision.date is None:
                continue
            current = earliest.get(decision.employee_id)
            if current is None or decision.date < current:
                earliest[decision.employee_id] = decision.date

        for employee_id, first_date in earliest.items():
            later = Decision.objects.filter(employee_id=employee_id, date__gte=first_date).order_by('date', 'pk')
            for decision in later:
                decision.calc()

    def get_priors(self):
        return Decision.objects.filter(
            employee = self.employee, date__lt = self.date
        )

    def we_as_str(self):
        return f'{self.years()}Ε {self.months()}Μ {self.days()}Η'
    
    def _applications_before_hire(self, applications):
        """Οι αιτήσεις/εμπειρίες που ξεκινούν πριν την πρόσληψη. Αν το
        Employee.date_hired λείπει (π.χ. εργαζόμενος που δημιουργήθηκε από
        import script), δεν λαμβάνεται υπόψη και δεν εφαρμόζεται φίλτρο."""
        date_hired = self.employee.date_hired
        if date_hired is None:
            return list(applications)
        return [app for app in applications if app.start_date < date_hired]

    def calc_in_year(self, year):
        all_apps = []
        # Calculate the work experience based on Existing Applications and Decisions

        # First get decision intervals based on applications
        all_apps = self._applications_before_hire(self.applications.all())

        current_intervals = [
            app.to_interval().trimmed_in_year(year) for app in all_apps if app.is_in_year(year)
        ]

        current_apps = [
            app for app in all_apps if app.is_in_year(year)
        ]

        # Then check decisions with prior date
        prior_decisions = Decision.objects.filter(date__lt = self.date, employee=self.employee).order_by('-date')

        prior_intervals = []
        for decision in prior_decisions:
            prior_apps = self._applications_before_hire(decision.applications.all())
            prior_intervals += [ app.to_interval() for app in prior_apps ]
            all_apps += prior_apps

        if len(prior_intervals) > 0:
            prior_map, prior_days = interval_map(prior_intervals)
            all_intervals = current_intervals + prior_intervals
        else:
            prior_days = 0
            prior_map = []
            all_intervals = current_intervals

        
        entire_map, all_days = interval_map(all_intervals)  
        
        total_days = all_days - prior_days

        y_prior, m_prior, d_prior = calc_ymd(prior_days, self._ymd_ref_date())
        y_all, m_all, d_all = calc_ymd(all_days, self._ymd_ref_date())
 
        orgs = { app.id : app.organization[:20] for app in all_apps}
        types = { app.id : app.get_type_display()[:40] for app in all_apps}
       
        return {
            'prior_map' : prior_map, 
            'entire_map' : entire_map, 
            'prior_days' : prior_days,
            'all_days' : all_days,
            'total_days' : total_days,
            'current_apps' : current_apps,
            
            'orgs' : orgs, 
            'types' : types,
            
            'd_current' : self.days,
            'm_current' : self.months,
            'y_current' : self.years,
            
            'd_prior' : d_prior,
            'm_prior' : m_prior,
            'y_prior' : y_prior,
            
            'd_all' : d_all,
            'm_all' : m_all,
            'y_all' : y_all,            
        }

    def calc(self, debug=False):

        all_apps = []
        # Calculate the work experience based on Existing Applications and Decisions

        # First get decision intervals based on applications
        all_apps = self._applications_before_hire(self.applications.all())
        current_intervals = [
            app.to_interval() for app in all_apps
        ]       
            
        # Then check decisions with prior date
        prior_decisions = Decision.objects.filter(date__lt = self.date, employee=self.employee).order_by('-date')

        prior_intervals = []
        for decision in prior_decisions:
            prior_apps = self._applications_before_hire(decision.applications.all())
            prior_intervals += [ app.to_interval() for app in prior_apps ]
            all_apps += prior_apps

        if len(prior_intervals) > 0:
            prior_map, prior_days = interval_map(prior_intervals)
            all_intervals = current_intervals + prior_intervals
        else:
            prior_days = 0
            prior_map = []
            all_intervals = current_intervals

        entire_map, all_days = interval_map(all_intervals)        
        self.total_days = math.floor(all_days - prior_days)
        self.save()
    
        y_prior, m_prior, d_prior = calc_ymd(prior_days, self._ymd_ref_date())
        y_all, m_all, d_all = calc_ymd(all_days, self._ymd_ref_date())
        
        orgs = { app.id : app.organization[:20] for app in all_apps}
        types = { app.id : app.get_type_display()[:40] for app in all_apps}
       
        if debug:
            print('='*80)
            print(f'Decision with id={self.id} contains the following applications:')
            for app in self.applications.all():
                print(app)

            print('Prior decisions:')
            if len(prior_decisions) == 0:
                print('None')
            else:
                for dec in prior_decisions:
                    print(dec)
                print('Map for prior decisions:')
                for el in prior_map:
                    print(el)
            print('Entire Map:')
            for el in entire_map:
                    print(el)
        apps = { app.id : app for app in all_apps }

        return {
            'prior_map' : prior_map, 
            'entire_map' : entire_map, 
            'prior_days' : prior_days,
            'all_days' : math.floor(all_days),
            'total_days' : math.floor(self.total_days),
            'apps' : apps,
            
            'orgs' : orgs, 
            'types' : types,
            
            'd_current' : self.days,
            'm_current' : self.months,
            'y_current' : self.years,
            
            'd_prior' : math.floor(d_prior),
            'm_prior' : m_prior,
            'y_prior' : y_prior,
            
            'd_all' : math.floor(d_all),
            'm_all' : m_all,
            'y_all' : y_all,            
        }
    
    def get_years(self):
        if self.applications:
            earliest_app = self.applications.order_by('start_date').first()
            latest_app = self.applications.order_by('end_date').last()
            year_start = earliest_app.start_date.year
            year_end = latest_app.end_date.year
            return list(range(year_start, year_end + 1))
        else:
            return []
        

    def calc_by_year(self):
        years = self.get_years()
        result = {}
        if len(years) > 0:
            for year in years:
                result[year] = self.calc_in_year(year)['total_days']

        return result


# Historical log of HR/payroll decisions (wage-step progression, rank/wage
# classification, prior-service recognition, degree-relevance recognition),
# imported from scanned official acts processed by the scandocs pipeline.
# Unlike WageClass/Reference (which only hold a single "current" reference
# point per employee), this model keeps one row per decision event.
class PayrollDecision(models.Model):

    WAGE_PROGRESSION = 'wage_progression'
    INDIVIDUAL_RANKING = 'individual_ranking'
    # Συλλογική κατάταξη λόγω αλλαγής νομοθετικού πλαισίου (πανεθνική ή
    # τμηματική) - καταγράφεται σαν ιστορικό γεγονός με τα ίδια ακριβώς
    # πεδία με το WAGE_PROGRESSION, αλλά ΔΕΝ την λαμβάνει υπόψη το
    # sync_employee_wage_class() (βλ. παρακάτω) - το "ρολόι" μέχρι το
    # επόμενο ΜΚ δεν ξεκινάει από την αρχή σε μία τέτοια αναδιάταξη,
    # συνεχίζει να μετράει από την τελευταία πραγματική
    # WAGE_PROGRESSION/INDIVIDUAL_RANKING. Παλαιότερα (πριν υπάρξει αυτό το
    # type) μία τέτοια αλλαγή νόμου αντιμετωπιζόταν σαν απλή
    # WAGE_PROGRESSION/INDIVIDUAL_RANKING ανά εργαζόμενο - λάθος, αφού
    # μηδένιζε το ρολόι.
    LEGAL_FRAMEWORK_RECLASSIFICATION = 'legal_framework_reclassification'
    # Αλλαγή ακαδημαϊκής βαθμίδας (π.χ. Επίκουρος -> Αναπληρωτής -> Καθηγητής),
    # μέσω πρυτανικής πράξης διορισμού μετά από κρίση/εξέλιξη - διαφορετικό
    # γεγονός από το INDIVIDUAL_RANKING (κατάταξη σε ΜΚ) ή το WAGE_PROGRESSION
    # (μισθολογική εξέλιξη εντός της ίδιας βαθμίδας). Η νέα βαθμίδα πάει στο
    # ήδη υπάρχον πεδίο `rank`. Το scandocs pipeline δεν σκανάρει/ταξινομεί
    # ακόμα τέτοιου είδους έγγραφα (βλ. συζήτηση) - προς το παρόν χειροκίνητη
    # καταχώρηση από την HR.
    RANK_PROMOTION = 'rank_promotion'
    # Αλλαγή διοικητικού βαθμού (Α, Β, Γ, Δ) του διοικητικού προσωπικού - ΔΕΝ
    # είναι το ίδιο με το RANK_PROMOTION (ακαδημαϊκή βαθμίδα, μόνο για ΔΕΠ).
    # Επαναχρησιμοποιεί το ίδιο πεδίο `rank` (π.χ. τιμή "Α", "Β", ...).
    GRADE_CHANGE = 'grade_change'
    # Αρχικός διορισμός (πρυτανική πράξη διορισμού) - καταγράφει τη βαθμίδα/
    # θέση ευθύνης εκκίνησης (πεδία `rank`/`responsibility_position`), όχι
    # το ΜΚ (αυτό ξεκινά με ξεχωριστή WAGE_PROGRESSION/INDIVIDUAL_RANKING
    # απόφαση). Νέο τύπο - από το scandocs employee_history.csv pipeline
    # (ιστορικό ανά εργαζόμενο, όχι το παλαιότερο department-level CSV).
    APPOINTMENT = 'appointment'
    # Ανάληψη καθηκόντων - το save() συμπληρώνει αυτόματα το
    # Employee.date_hired από αυτόν τον τύπο, μόνο όταν είναι ακόμα κενό
    # (βλ. sync_employee_date_hired παρακάτω).
    DUTY_ASSUMPTION = 'duty_assumption'
    # PRIOR_SERVICE_RECOGNITION = υπολογιζόμενη από το σύστημα (βλ.
    # sync_from_linked_decision παρακάτω). PRIOR_SERVICE_RECOGNITION_LEGACY =
    # παλαιά/εισαγόμενα δεδομένα (π.χ. scandocs/employees.csv), πλήρως
    # χειροκίνητα πεδία - ο μελλοντικός importer θα στοχεύει σε αυτό το type.
    PRIOR_SERVICE_RECOGNITION = 'prior_service_recognition'
    PRIOR_SERVICE_RECOGNITION_LEGACY = 'prior_service_recognition_legacy'
    MASTERS_RELEVANCE_RECOGNITION = 'masters_relevance_recognition'
    PHD_RELEVANCE_RECOGNITION = 'phd_relevance_recognition'

    DECISION_TYPE_CHOICES = (
        (WAGE_PROGRESSION, _('Μισθολογική εξέλιξη')),
        (INDIVIDUAL_RANKING, _('Μισθολογική κατάταξη')),
        (LEGAL_FRAMEWORK_RECLASSIFICATION, _('Συλλογική κατάταξη (αλλαγή νομοθετικού πλαισίου)')),
        (RANK_PROMOTION, _('Εξέλιξη/Προαγωγή βαθμίδας')),
        (GRADE_CHANGE, _('Αλλαγή βαθμού')),
        (APPOINTMENT, _('Διορισμός')),
        (DUTY_ASSUMPTION, _('Ανάληψη καθηκόντων')),
        (PRIOR_SERVICE_RECOGNITION, _('Αναγνώριση προϋπηρεσίας')),
        (PRIOR_SERVICE_RECOGNITION_LEGACY, _('Αναγνώριση προϋπηρεσίας (παλαιά καταχώρηση)')),
        (MASTERS_RELEVANCE_RECOGNITION, _('Αναγνώριση συνάφειας μεταπτυχιακού')),
        (PHD_RELEVANCE_RECOGNITION, _('Αναγνώριση συνάφειας διδακτορικού')),
    )

    employee = models.ForeignKey(Employee, null=True, on_delete=models.SET_NULL, related_name='payroll_decisions')

    decision_type = models.CharField(max_length=50, choices=DECISION_TYPE_CHOICES, null=True)

    decision_date = models.DateField(null=True, blank=True, help_text=_('Ημερομηνία πράξης'))
    effective_date = models.DateField(null=True, blank=True, help_text=_('Ημερομηνία ισχύος'))

    protocol_number = models.CharField(max_length=100, null=True, blank=True, help_text=_('Αριθμός πρωτοκόλλου'))

    wage_class = models.PositiveIntegerField(null=True, blank=True, help_text=_('Μισθολογικό κλιμάκιο (το Χ από ΜΚ-Χ)'))
    rank = models.CharField(max_length=100, null=True, blank=True, help_text=_('Βαθμίδα'))
    # Εκλεγμένη/διοικητική θέση ευθύνης (π.χ. Κοσμήτορας, Πρύτανης) -
    # ανεξάρτητο από decision_type, μπορεί να εμφανιστεί σε οποιαδήποτε
    # γραμμή έχει τιμή στη στήλη "θέση_ευθύνης" του employee_history.csv.
    responsibility_position = models.CharField(max_length=200, null=True, blank=True, help_text=_('Θέση ευθύνης (π.χ. Κοσμήτορας, Πρύτανης)'))
    # Θέσεις ευθύνης έχουν συνήθως ορισμένη θητεία (π.χ. 3 έτη για
    # Κοσμήτορα) - συμπληρώνεται χειροκίνητα από την HR όταν είναι γνωστή,
    # καμία αυτόματη λογική/υπολογισμός δεν εξαρτάται από αυτό το πεδίο.
    term_end_date = models.DateField(null=True, blank=True, help_text=_('Λήξη θητείας (για θέσεις ευθύνης με ορισμένη διάρκεια)'))
    legal_framework = models.CharField(max_length=100, null=True, blank=True, help_text=_('Νομοθετικό πλαίσιο'))

    justification = models.TextField(null=True, blank=True, help_text=_('Αιτιολογία'))

    prior_service_years = models.PositiveIntegerField(null=True, blank=True, help_text=_('Προϋπηρεσία (έτη)'))
    prior_service_months = models.PositiveIntegerField(null=True, blank=True, help_text=_('Προϋπηρεσία (μήνες)'))
    prior_service_days = models.PositiveIntegerField(null=True, blank=True, help_text=_('Προϋπηρεσία (ημέρες)'))
    total_prior_service_days = models.FloatField(
        null=True, blank=True,
        help_text=_('Συνολικές ημέρες αναγνωρισμένης προϋπηρεσίας (υπολογίζονται από τη συνδεδεμένη Απόφαση)'),
    )

    source_file_path = models.CharField(max_length=500, null=True, blank=True, help_text=_('Σχετική διαδρομή αρχείου στο scandocs'))
    document = models.FileField(upload_to=hrms_payroll_decision_dir, null=True, blank=True, help_text=_('Πράξη/Απόφαση (PDF)'))
    alternate_files = models.TextField(null=True, blank=True, help_text=_('Εναλλακτικά/διπλότυπα αρχεία πηγής'))

    # Συνοδευτικά έγγραφα του ίδιου γεγονότος πέρα από την ίδια την πράξη
    # (`document` πάνω) - από το scandocs employee_history.csv pipeline, το
    # οποίο μπορεί να παράγει έως 4 επιπλέον PDF ανά γεγονός. Ένα πεδίο ανά
    # ρόλο αντί για ξεχωριστό μοντέλο, ώστε να εμφανίζονται στις υπάρχουσες
    # φόρμες χωρίς νέο UI. Τα *_source_file_path είναι bookkeeping του
    # importer, όπως και το source_file_path πάνω - δεν μπαίνουν σε καμία
    # φόρμα της HR (βλ. PAYROLL_DECISION_FIELDS στο hrms/forms.py).
    summary_document = models.FileField(upload_to=hrms_payroll_decision_dir, null=True, blank=True, help_text=_('Περίληψη Πράξης (PDF)'))
    summary_source_file_path = models.CharField(max_length=500, null=True, blank=True)

    transmittal_document = models.FileField(upload_to=hrms_payroll_decision_dir, null=True, blank=True, help_text=_('Διαβιβαστικό (PDF)'))
    transmittal_source_file_path = models.CharField(max_length=500, null=True, blank=True)

    oath_document = models.FileField(upload_to=hrms_payroll_decision_dir, null=True, blank=True, help_text=_('Πρωτόκολλο Ορκωμοσίας (PDF)'))
    oath_source_file_path = models.CharField(max_length=500, null=True, blank=True)

    duty_assumption_document = models.FileField(upload_to=hrms_payroll_decision_dir, null=True, blank=True, help_text=_('Πρωτόκολλο Ανάληψης Καθηκόντων (PDF)'))
    duty_assumption_source_file_path = models.CharField(max_length=500, null=True, blank=True)

    notes = models.TextField(null=True, blank=True, help_text=_('Παρατηρήσεις'))

    # Optional, HR-assigned cross-reference to the corresponding Decision in
    # the live Application/Decision recognition system - mainly meaningful
    # for decision_type == PRIOR_SERVICE_RECOGNITION. Decision's own model
    # and calc() logic are untouched by this link.
    linked_decision = models.ForeignKey(
        Decision, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='linked_payroll_decisions',
        help_text=_('Αντίστοιχη Απόφαση Αναγνώρισης στο σύστημα (κυρίως για αναγνώριση προϋπηρεσίας)'),
    )

    def linked_decision_display(self):
        if not self.linked_decision:
            return ''
        return self.linked_decision.ref_no or str(self.linked_decision)

    def sync_from_linked_decision(self):
        """Για decision_type == PRIOR_SERVICE_RECOGNITION (υπολογιζόμενη από
        το σύστημα): αντλεί ημερομηνία πράξης, αριθμό πρωτοκόλλου, αρχείο
        απόφασης και στοιχεία προϋπηρεσίας από τη συνδεδεμένη Decision.
        Καλεί πρώτα decision.calc() ώστε τα νούμερα να είναι ενημερωμένα.
        No-op αν δεν υπάρχει linked_decision."""
        decision = self.linked_decision
        if not decision:
            return
        decision.calc()
        self.decision_date = decision.date
        self.protocol_number = decision.ref_no
        self.document = decision.document
        self.total_prior_service_days = decision.total_days
        self.prior_service_years = decision.years()
        self.prior_service_months = decision.months()
        self.prior_service_days = decision.days()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Μετά από save() μισθολογικής εξέλιξης/κατάταξης, το WageClass του
        # εργαζομένου επανυπολογίζεται από την πιο πρόσφατη (μεγαλύτερο
        # effective_date) τέτοια απόφαση - όχι απαραίτητα αυτή που μόλις
        # αποθηκεύτηκε (π.χ. αν εισάγεται/διορθώνεται μία παλαιότερη
        # απόφαση ενώ υπάρχει ήδη νεότερη, το WageClass δεν πρέπει να
        # αλλάξει). Στο save() και όχι με signal, όπως ζητήθηκε.
        if self.employee_id and self.decision_type in (self.WAGE_PROGRESSION, self.INDIVIDUAL_RANKING):
            self.sync_employee_wage_class()
        # Ίδια λογική για το RankClass (βαθμίδα ΔΕΠ / βαθμός διοικητικού) -
        # RANK_PROMOTION/GRADE_CHANGE δεν προβλέπουν "επόμενη" τιμή σαν το
        # WageClass, απλά καταγράφουν την τρέχουσα. Το APPOINTMENT
        # (αρχικός διορισμός) συμπεριλαμβάνεται επίσης - συχνά καταγράφει
        # την αρχική βαθμίδα, πριν υπάρξει καμία RANK_PROMOTION.
        if self.employee_id and self.decision_type in (self.RANK_PROMOTION, self.GRADE_CHANGE, self.APPOINTMENT):
            self.sync_employee_rank_class()
        # Ανάληψη καθηκόντων -> συμπληρώνει το Employee.date_hired, μόνο αν
        # είναι ακόμα κενό (βλ. sync_employee_date_hired).
        if self.employee_id and self.decision_type == self.DUTY_ASSUMPTION:
            self.sync_employee_date_hired()

    def sync_employee_wage_class(self):
        """Θέτει το WageClass(employee) του εργαζομένου ίσο με το
        ref_date/ref_value της πιο πρόσφατης (μεγαλύτερο effective_date)
        απόφασης τύπου WAGE_PROGRESSION/INDIVIDUAL_RANKING που έχει
        καταχωρηθεί για αυτόν - αγνοεί αποφάσεις χωρίς effective_date ή
        wage_class (καμία αξιόπιστη τιμή για σύγκριση/χρήση). No-op αν δεν
        υπάρχει καμία τέτοια απόφαση.

        Σκόπιμα ΔΕΝ περιλαμβάνει το LEGAL_FRAMEWORK_RECLASSIFICATION εδώ -
        μία συλλογική κατάταξη λόγω αλλαγής νόμου δεν πρέπει να μηδενίζει
        το ρολόι μέχρι το επόμενο ΜΚ. Μην το προσθέσεις."""
        latest = PayrollDecision.objects.filter(
            employee=self.employee,
            decision_type__in=(self.WAGE_PROGRESSION, self.INDIVIDUAL_RANKING),
            effective_date__isnull=False,
            wage_class__isnull=False,
        ).order_by('-effective_date', '-pk').first()
        if not latest:
            return
        wage_class, _created = WageClass.objects.get_or_create(employee=self.employee)
        wage_class.ref_date = latest.effective_date
        wage_class.ref_value = latest.wage_class
        wage_class.save()

    def sync_employee_rank_class(self):
        """Θέτει το RankClass(employee) του εργαζομένου ίσο με το
        ref_date/rank της πιο πρόσφατης (μεγαλύτερο effective_date)
        απόφασης τύπου RANK_PROMOTION/GRADE_CHANGE/APPOINTMENT που έχει
        καταχωρηθεί για αυτόν - ίδια λογική με sync_employee_wage_class().
        Το APPOINTMENT συμπεριλαμβάνεται γιατί συχνά καταγράφει την αρχική
        βαθμίδα διορισμού. Αγνοεί αποφάσεις χωρίς effective_date ή χωρίς
        τιμή στο rank. No-op αν δεν υπάρχει καμία τέτοια απόφαση."""
        latest = PayrollDecision.objects.filter(
            employee=self.employee,
            decision_type__in=(self.RANK_PROMOTION, self.GRADE_CHANGE, self.APPOINTMENT),
            effective_date__isnull=False,
        ).exclude(rank__isnull=True).exclude(rank='').order_by('-effective_date', '-pk').first()
        if not latest:
            return
        rank_class, _created = RankClass.objects.get_or_create(employee=self.employee)
        rank_class.ref_date = latest.effective_date
        rank_class.rank = latest.rank
        rank_class.save()

    def sync_employee_date_hired(self):
        """Αν το Employee.date_hired είναι ακόμα κενό, το συμπληρώνει από
        την παλαιότερη (μικρότερη ημερομηνία) καταχωρημένη DUTY_ASSUMPTION
        απόφαση του εργαζομένου (effective_date, ή decision_date αν αυτή
        λείπει) - ποτέ δεν αντικαθιστά ήδη υπάρχουσα τιμή (πιθανόν
        χειροκίνητα καταχωρημένη από την HR). No-op αν δεν υπάρχει καμία
        τέτοια απόφαση με χρησιμοποιήσιμη ημερομηνία."""
        if self.employee.date_hired:
            return
        dates = [
            d.effective_date or d.decision_date
            for d in PayrollDecision.objects.filter(employee=self.employee, decision_type=self.DUTY_ASSUMPTION)
        ]
        dates = [d for d in dates if d]
        if not dates:
            return
        self.employee.date_hired = min(dates)
        self.employee.save(update_fields=['date_hired'])

    def __str__(self):
        return f'{self.employee}, {self.get_decision_type_display()}, {self.decision_date}'

    class Meta:
        ordering = ['-effective_date', '-decision_date']

