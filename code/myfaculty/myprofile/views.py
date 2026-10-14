from django.db.models.query import QuerySet
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .models import StaffMember, Associate, Student, PersonalInfo
from .checks import is_staff_member, is_associate, is_secreteriat, is_internal_staff_member, is_student, app_urls, is_department_secreteriat, is_hr_user
from .forms import StaffFormRestricted, AssociateFormRestricted, AssociateForm, StaffForm, StudentFormRestricted, SignUpForm, RegisterForm, PasswordForm, ForgotPasswordForm, ProfileForm, SecProfileForm, HrPIForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import generic
from dal import autocomplete
from theses.models import Thesis
import csv
from django.contrib.auth import get_user_model, logout, update_session_auth_hash
from django.core.signing import TimestampSigner,SignatureExpired, BadSignature
from django.conf import settings
from mailer.gmail import notify
from django.utils.safestring import mark_safe
from .utils import get_domain_uri, send_password_link
from django.utils.translation import gettext_lazy as _
from myprofile.utils import complexity_message
from scopes.utils import get_scoped_object_or_exc, get_secreteriat_scope
from myprofile.utils import get_domain_uri
from django.core.exceptions import PermissionDenied
from core.views import StaffUpdateView, ScopedSecUpdateView
import base64
from django.core.files.base import ContentFile
import uuid


User = get_user_model()


# Create your views here.


def render_anauthorized_staff(request):
     msg1 = _('Δεν είστε δηλωμένος στο σύστημα ως μέλος του ιδρύματος.')
     return render(request, 'myprofile/message.html',
                       context = {'message' : msg1 }                                  )

@login_required
def staff_profile(request):
    profile = StaffMember.objects.get(user = request.user)
    if request.method == 'POST':
        form = StaffFormRestricted(request.POST, instance = profile)

        if form.is_valid():
            form.save()
            return reverse_lazy('myprofile:index')
        else:
            return render(request, 'myprofile/profile.html', context = {'form' : form})
    else:
        form = StaffFormRestricted(instance=profile)
        return render(request, 'myprofile/profile.html', context={'form' : form})

@login_required
def associate_profile(request):
    profile = Associate.objects.get(user = request.user)
    if request.method == 'POST':
        form = AssociateFormRestricted(request.POST, instance = profile)
        if form.is_valid():
            form.save()
            return redirect('myprofile:index')
        else:
            return render(request, 'myprofile/profile.html', context = {'form' : form})
    else:
        form = AssociateFormRestricted(instance = profile)
        return render(request, 'myprofile/profile.html', context={'form' : form})

@login_required
def student_profile(request):
    profile = get_object_or_404(Student, user = request.user)
    form = StudentFormRestricted(instance = profile)
    thesis = Thesis.objects.filter(assigned_to = profile)
    if thesis.count() == 1:
        thesis = thesis[0]
    else:
        thesis = None
    
    return render(request, 'myprofile/studentprofile.html', context={'form' : form, 'thesis' : thesis})

@login_required
def index(request):
    if is_secreteriat(request.user):
        return redirect('myprofile:dashboard')
    elif is_staff_member(request.user) :
        return redirect('myprofile:dashboard')        
    elif is_associate(request.user):
        return redirect('myprofile:dashboard')
    elif is_student(request.user):
        return redirect('myprofile:dashboard') 
    
    return redirect('myprofile:dashboard')
@login_required
def logout_view(request):
    logout(request)
    msg1 = _('Αποσυνδεθήκατε από το σύστημα. Ευχαριστούμε που χρησιμοποιήσατε την υπηρεσία μας. ')
    msg2 = _('Συνδεθείτε ξανά')
    here = _('εδώ')
    return render(request, 
                  'myprofile/message.html', 
                  context = {'message' : 
                             """
                             %s </br> </br>
                             %s <a href="%s"> %s </a>
                             """ %( msg1, msg2, reverse_lazy('myprofile:index'), here) })
                             
class list_associates(UserPassesTestMixin, LoginRequiredMixin, generic.ListView):
    
    template_name = "myprofile/list_associates.html"
    context_object_name = "associates"

    def test_func(self):
        return is_department_secreteriat(self.request.user)

    def get_queryset(self):
        return Associate.objects.sc_filter(user=self.request.user)
    
class edit_associate(UserPassesTestMixin, LoginRequiredMixin, generic.UpdateView):
    model = Associate
    template_name = "myprofile/profile.html"
    form_class = AssociateForm
    success_url = reverse_lazy('myprofile:list_associates')

    def get_object(self, queryset=None):
        obj = super().get_object(queryset = queryset)
        obj.in_scope_or_403(self.request.user)
        return obj

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        return is_department_secreteriat(self.request.user)
    
class create_associate(UserPassesTestMixin, LoginRequiredMixin, generic.CreateView):
    model = Associate
    template_name = "myprofile/profile.html"
    form_class = AssociateForm
    success_url = reverse_lazy('myprofile:list_associates')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        return is_department_secreteriat(self.request.user)

class staff_list_associates(UserPassesTestMixin, LoginRequiredMixin, generic.ListView):
    
    template_name = "myprofile/staff_list_associates.html"
    context_object_name = "associates"

    def test_func(self):
        return is_internal_staff_member(self.request.user)

    def get_queryset(self):
        p = StaffMember.objects.get(user = self.request.user)
        return Associate.objects.filter(supervisor = p)

class staff_edit_associate(UserPassesTestMixin, LoginRequiredMixin, generic.UpdateView):
    model = Associate
    template_name = "myprofile/associate.html"
    form_class = AssociateFormRestricted
    success_url = reverse_lazy('myprofile:staff_list_associates')

    def test_func(self):      
        return is_internal_staff_member(self.request.user) 

    def get_queryset(self):
        q = super().get_queryset()
        p = StaffMember.objects.get(user = self.request.user)        
        return q.filter(supervisor = p)

class staff_create_associate(UserPassesTestMixin, LoginRequiredMixin, generic.CreateView):
    model = Associate
    template_name = "myprofile/profile.html"
    form_class = AssociateFormRestricted
    success_url = reverse_lazy('myprofile:staff_list_associates')

    def test_func(self):      
        return is_internal_staff_member(self.request.user) 
    
    def form_valid(self, form):
        supervisor = get_object_or_404(StaffMember, user = self.request.user)
        obj = form.save(commit = False)
        obj.supervisor = supervisor
        obj.save()
        return super().form_valid(form)
    
@login_required
@user_passes_test(is_secreteriat)    
def delete_associate(request, pk):
    obj = get_object_or_404(Associate, pk=pk)
    obj.delete()
    return redirect('myprofile:list_associates')
    
@login_required
@user_passes_test( is_internal_staff_member)    
def staff_delete_associate(request, pk):
    p = StaffMember.objects.get(user = request.user)
    obj = get_object_or_404(Associate, pk=pk, supervisor=p)
    obj.delete()
    return redirect('myprofile:staff_list_associates')

"""
Faculty CRUD views
"""

class list_staff(UserPassesTestMixin, LoginRequiredMixin, generic.ListView):
    
    template_name = "myprofile/list_staff.html"
    context_object_name = "staff"

    def test_func(self):
        return is_department_secreteriat(self.request.user)

    def get_queryset(self):
        return StaffMember.objects.sc_filter(user=self.request.user)    
    
class edit_staff(UserPassesTestMixin, LoginRequiredMixin, generic.UpdateView):
    model = StaffMember
    template_name = "myprofile/staff_edit.html"
    form_class = StaffForm
    success_url = reverse_lazy('myprofile:list_staff')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['back_url'] = reverse_lazy('myprofile:list_staff')
        context['can_edit'] = self.object.can_edit(self.request.user)
        return context
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset = queryset)
        obj.in_scope_or_403(self.request.user)
        return obj
        
    def test_func(self):
        return is_department_secreteriat(self.request.user)

class create_staff(UserPassesTestMixin, LoginRequiredMixin, generic.CreateView):
    model = StaffMember
    template_name = "myprofile/staff_edit.html"
    form_class = StaffForm
    success_url = reverse_lazy('myprofile:list_staff')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def test_func(self):
        return is_department_secreteriat(self.request.user)

@login_required
@user_passes_test(is_secreteriat)
@user_passes_test(is_department_secreteriat)

def delete_staff(request, pk):
    obj = get_object_or_404(StaffMember, pk=pk)
    if obj.can_edit(request.user):
        obj.delete()
    else:
        raise PermissionDenied
    
    return redirect('myprofile:list_staff')

class SecScopedPhDStudentAutoComplete(LoginRequiredMixin, UserPassesTestMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):        
        from curricula.models import StudyProgram
        scopes = get_secreteriat_scope(self.request.user)
        doctoral_progs = scopes['programs'].filter(type = StudyProgram.DOCTORAL)
        if self.q:
            qs = Student.objects.filter(display_name__contains=self.q, program__in=doctoral_progs )            
        return qs[:10]
    
    def test_func(self):
        return is_secreteriat(self.request.user)

class StaffMemberAutocomplete(LoginRequiredMixin, UserPassesTestMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):        
        if self.q:
            qs = StaffMember.objects.filter(display_name__contains=self.q) | StaffMember.objects.filter(display_name_en__contains=self.q)
        return qs[:10]
    
    def test_func(self):
        return is_staff_member(self.request.user) or is_secreteriat(self.request.user) or is_student(self.request.user)

class UserAutocomplete(LoginRequiredMixin, autocomplete.Select2QuerySetView):
    def get_queryset(self):
        User = get_user_model()
        qs = User.objects.all()
        if self.q:
            qs = qs.filter(display_name__contains=self.q)
        
        return qs[:10]

class StudentAutocomplete(UserPassesTestMixin, LoginRequiredMixin, autocomplete.Select2QuerySetView):
    
    def test_func(self):
        return is_secreteriat(self.request.user) or is_staff_member(self.request.user)

    def get_queryset(self):
        if self.q:  
            q = str(self.q)
            if len(q) >= 3:
                qs = Student.objects.filter(display_name__contains=q) | Student.objects.filter(reg_num__contains = q)
                return qs[:10]

    # def get_list(self):
    #     entries = sis.estudiesdb().filter_students(self.q)
    #     if not entries:
    #         return []
    #     else:
    #         return [ [ e['UserName'], e['SurName'] + ' ' + e['FirstName'] + ' (' + e['UserName'] + ')' ] for e in entries ]
    #         #return [ [ e['UserName'], e['UserName'] ] for e in entries ]
            
@login_required
@user_passes_test(is_secreteriat)
def export_associate_csv(request):
        
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'},
    )

    writer = csv.writer(response, delimiter=';', quoting = csv.QUOTE_ALL)        
    objs = Associate.objects.all().order_by('last_update')
    i = 0
    for obj in objs:
        d = obj.to_dict()
        if i==0:
            writer.writerow(d.keys())
        l = [d[k] for k in d.keys()]
        i += 1
        writer.writerow(l)

    return response

def export_staff_csv(request):
        
    response = HttpResponse(
        content_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="export.csv"'},
    )

    writer = csv.writer(response, delimiter=';', quoting = csv.QUOTE_ALL)        
    objs = StaffMember.objects.all().order_by('surname')
    i = 0
    for obj in objs:
        d = obj.to_dict()
        if i==0:
            writer.writerow(d.keys())
        l = [d[k] for k in d.keys()]
        i += 1
        writer.writerow(l)

    return response

def signup(request, token):
    logout(request)
    signer = TimestampSigner()
    try:
        unsigned = signer.unsign_object(token,max_age=settings.INVITATION_REFERENCE_MAX_AGE_SECS)
        email = unsigned['email']
    except SignatureExpired:
        message = _('H πρόκληση να εγγραφείτε έχει λήξει. Θα πρέπει να επαναλάβετε την διαδικασία.')            
        return render(request,'myprofile/message.html', context = {'message' : message})
        
    except BadSignature:
        message = _('O σύνδεσμος δεν είναι σωστός!')            
        return render(request,'myprofile/message.html', context = {'message' : message})      
    
    UserModel = get_user_model()        
       
    if UserModel.objects.filter(username = email).count()>0:
        message = _('Έχετε ήδη εγγραφεί στο σύστημα!')
        return render(request,'myprofile/message.html', context = {'message' : message})      
    
    if request.method == "POST":         

        form = SignUpForm(request.POST, email=email)
        if form.is_valid():
            cleaned_data=form.cleaned_data
            email = cleaned_data['email']
            name = cleaned_data['name']
            surname = cleaned_data['surname']
            password = cleaned_data['password1']
            user = UserModel.objects.create_user(email, email=email, password=password, first_name=name, last_name=surname )
            user.save()
            return redirect('myprofile:signup_success')
        else:
            alertclass = "alert alert-info"

    else:
        form = SignUpForm(email=email)
        alertclass = "alert alert-info"

    return render(request, "myprofile/signup.html", {"form": form, "password_policy" : mark_safe(complexity_message()), "alertclass" : alertclass })

def signup_success(request):
    msg1 = _('Εγγραφήκατε επιτυχώς στο σύστημα!')
    msg2 = _('Συνδεθείτε ξανά')
    msg3 = _('εδώ')
    return render(request, 
                  'myprofile/message.html', 
                  context = {'message' : 
                             """
                             %s </br></br>                             
                             %s <a href="%s"> %s </a>
                             """ %(msg1, msg2, reverse_lazy('myprofile:index'), msg3) })

def register(request):
   back_url = reverse_lazy('myprofile:index')
   domain = get_domain_uri(request)
   if request.method == "POST":
        
        form = RegisterForm(request.POST)
        if form.is_valid():
            signer = TimestampSigner()
            email = form.cleaned_data['email1']
            signed_data = signer.sign_object({'email' : email})            
            url = domain + reverse_lazy('myprofile:signup', kwargs = {'token' : signed_data})
            message_body = settings.REGISTRATION_MESSAGE.format(url=url)
            notify.delay(email, settings.REGISTRATION_SUBJECT, message_body)
            return redirect('myprofile:register_success')
        else:
            return render(request, "myprofile/register.html", {"form": form, "back_url" : back_url })
   else:
       form = RegisterForm()
   return render(request, "myprofile/register.html", {"form": form, "back_url" : back_url })

def register_success(request):
    return render(request, 
                  'myprofile/message.html', 
                  context = {'message' : _('Έχει αποσταλλεί e-mail στην διεύθυνση που δηλώσατε για να ενεργοποιήσετε το λογαριασμό σας') } )

# Landing page for apps destined for the general public (after registration)
@login_required
def dashboard(request):

    user = request.user
    apps = app_urls(user)    
    return render(request,
                  'myprofile/landing.html',
                  context = {'apps' : apps}
                  )

@login_required
def password_change(request):
    user = request.user
    success_url = reverse_lazy('myprofile:dashboard')
    
    if settings.INTERNAL_DOMAIN in user.email:
        msg1 = _('Είστε ιδρυματικός χρήστης. Θα πρέπει να αλλάξετε τον κωδικό χρησιμοποιώντας τα κεντρικά συστήματα του ιδρύματος')
        msg2 = _('Επιστροφή')
        message = """
                <p> %s </p>
                <a href="%s" class="alert-link"> %s </a>
                """ %(msg1, success_url, msg2)        
        return render(request, 'myprofile/message.html', context={'message' : mark_safe(message) })
   
    if request.method == 'POST':
        form = PasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.save()
            update_session_auth_hash(request, user)
            msg1 = _('Ο κωδικός σας έχει αλλάξει.')
            msg2 = _('Επιστροφή')
            message = """
                <p> %s </p>
                </br>
                <a href="%s" class="alert-link"> %s </a>
                """ %(msg1, success_url, msg2)
            return render(request, 'myprofile/message.html', 
                          context={
                              'message' : mark_safe(message),
                              'back_url' : success_url })
    else:
        form = PasswordForm()
    
    return render(request, "myprofile/changepassword.html", 
                  context = {"form": form, "password_policy" : mark_safe(complexity_message()) , 
                             "alertclass" : "alert alert-info",
                             "back_url" : success_url })

def forgot_password(request):
    back_url = reverse_lazy('myprofile:index')
    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email1']
            send_password_link(request, email)
            msg = _('Παρακαλούμε ελέγξτε την διεύθυνση ηλεκτρονικού ταχυδρομείου που καταχωρήσατε για την συνέχεια.')
            message = """
                <p> %s </p>
            """ % msg
            return render(request, 'myprofile/message.html', context={'message' : mark_safe(message), "back_url" : back_url })
        else:
            return render(request, "myprofile/forgotpassword.html", {"form": form, "back_url" : back_url}) 
    else:
        form = ForgotPasswordForm()
        return render(request, "myprofile/forgotpassword.html", {"form": form, "back_url" : back_url})
    

def password_reset_choice(request):
    return render(request, 'myprofile/password_reset_choice.html')

def password_token(request, token):
    signer = TimestampSigner()
    try:
        invitation = signer.unsign_object(token,max_age = settings.PASSWORD_RESET_LINK_AGE)
    except SignatureExpired:
        message = _('Ο σύνδεσμος αυτός έχει λήξει.')
        return render(request,'myprofile/message.html', context = {'message' : message})        
    except BadSignature:
        message = _('O σύνδεσμος δεν είναι σωστός!')            
        return render(request,'myprofile/message.html', context = {'message' : message})  
    email = invitation['email']
    UserModel = get_user_model()
    user = get_object_or_404(UserModel, email = email)
    if request.method == 'POST':
        form = PasswordForm(request.POST)        
        if form.is_valid():
            password = form.cleaned_data['password1']
            user.set_password(password)
            user.save()
            success_url = reverse_lazy('myprofile:dashboard')
            msg1 = _('Ο κωδικός σας έχει αλλάξει.')
            msg2 = _('Επιστροφή')
            message = """
                <p> %s </p>
                </br>
                <a href="%s" class="alert-link">%s</a>
                """ %(msg1, success_url, msg2)
            return render(request, 'myprofile/message.html', context={'message' : mark_safe(message) })
    else:
        form = PasswordForm()
    
    return render(request, "myprofile/changepassword.html", {"form": form, "password_policy" : mark_safe(complexity_message()) , "alertclass" : "alert alert-info"})


class profile_update(StaffUpdateView):

    form_class = ProfileForm
    model = PersonalInfo
    success_url = reverse_lazy('myprofile:index')
    back_url = reverse_lazy('myprofile:index')
    required_extra = ['']
    
    def get_object(self):
        pi = get_object_or_404(PersonalInfo, user=self.request.user)
        return pi

    def form_valid(self, form):
        cropped_data = self.request.POST.get('cropped_image')

        if cropped_data:
            try:
                format, imgstr = cropped_data.split(';base64,')
                ext = format.split('/')[-1]
                unique_name = f"pic{uuid.uuid4().hex}.{ext}"
                file = ContentFile(
                    base64.b64decode(imgstr),
                    name=unique_name,
                )    
                form.instance.pic = file
            except Exception as e:
                print('Crop error: ', e)

        response = super().form_valid(form)
        
        return response        

class sec_profile_update(ScopedSecUpdateView):

    form_class = SecProfileForm
    model = PersonalInfo
    success_url = reverse_lazy('myprofile:list_staff')
    back_url = reverse_lazy('myprofile:list_staff')
        
    def form_valid(self, form):
        cropped_data = self.request.POST.get('cropped_image')

        if cropped_data:
            try:
                format, imgstr = cropped_data.split(';base64,')
                ext = format.split('/')[-1]
                unique_name = f"pic{uuid.uuid4().hex}.{ext}"
                file = ContentFile(
                    base64.b64decode(imgstr),
                    name=unique_name,
                )    
                form.instance.pic = file
            except Exception as e:
                print('Crop error: ', e)

        response = super().form_valid(form)
        
        return response        
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context 























