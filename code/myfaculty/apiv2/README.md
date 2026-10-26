# apiv2 — REST API ανά ρόλο

REST API (Django REST Framework) με πλήρες CRUD και αναζήτηση στα μοντέλα της εφαρμογής, με ξεχωριστά prefix ανά ρόλο. Σχεδιάστηκε ώστε να το καλεί αυτοματοποιημένα ένας MCP server ή άλλο script, με token ανά ρόλο.

| Prefix | Ποιος | Τι βλέπει |
|---|---|---|
| `/apiv2/<app>/<model>/` | admin (superuser) | Όλα τα μοντέλα, όλες οι εγγραφές |
| `/apiv2/hr/<app>/<model>/` | τμήμα προσωπικού (`scopes.HrStaff`) | Μοντέλα hrms και προσωπικού, όλες οι εγγραφές |
| `/apiv2/sec/<app>/<model>/` | γραμματείες (`scopes.Secretariat`) | Μόνο εγγραφές του scope της γραμματείας (προγράμματα/τμήματα) |

Ο superuser έχει πρόσβαση και στα τρία prefix. Στο `sec/` ο superuser βλέπει όλες τις εγγραφές, χωρίς περιορισμό scope.

Το API root κάθε prefix (`/apiv2/`, `/apiv2/hr/`, `/apiv2/sec/`) απαριθμεί τους διαθέσιμους πόρους.

## Αυθεντικοποίηση

Χρησιμοποιείται το `rest_framework.authtoken`. Κάθε αίτημα στέλνει την κεφαλίδα:

```
Authorization: Token <token>
```

Ο χρήστης και το token δημιουργούνται ως εξής:

- Στο Django admin (Auth Token → Tokens), ή
- από τη γραμμή εντολών: `docker compose exec web python manage.py drf_create_token <username>`, ή
- με POST `username`/`password` στο `/<γλώσσα>/api/auth/` (π.χ. `/el/api/auth/`) που επιστρέφει `{"token": "..."}`.

Για αυτοματοποιημένη χρήση (MCP) συνιστάται ένας ξεχωριστός service χρήστης ανά ρόλο, με τα ελάχιστα δικαιώματα:

- ο χρήστης με token για το `hr/` πρέπει να έχει εγγραφή `scopes.HrStaff`,
- ο χρήστης με token για το `sec/` πρέπει να έχει `scopes.Secretariat` με τα προγράμματα και τα τμήματα που θα βλέπει.

Παράδειγμα:

```bash
TOKEN=...
curl -H "Authorization: Token $TOKEN" http://localhost:30100/apiv2/hr/hrms/application/?employee=12
```

Επιπλέον, ένας superuser που έχει κάνει login στο site μπορεί να χρησιμοποιήσει το browsable API χωρίς token (session authentication).

## Endpoints και μέθοδοι

Για κάθε μοντέλο `<app>/<model>` (το `<model>` με πεζά, π.χ. `hrms/application`, `myprofile/student`):

| Μέθοδος | URL | Ενέργεια |
|---|---|---|
| GET | `…/<app>/<model>/` | Λίστα με σελιδοποίηση και αναζήτηση |
| POST | `…/<app>/<model>/` | Δημιουργία |
| GET | `…/<app>/<model>/<pk>/` | Μία εγγραφή |
| PUT | `…/<app>/<model>/<pk>/` | Πλήρης ενημέρωση |
| PATCH | `…/<app>/<model>/<pk>/` | Μερική ενημέρωση |
| DELETE | `…/<app>/<model>/<pk>/` | Διαγραφή |

Η εγγραφή που αλλάζει ή διαγράφεται δίνεται πάντα στο URL (`<pk>`), ποτέ στο query ή στο σώμα του αιτήματος.

Τα σώματα αιτημάτων είναι JSON (`Content-Type: application/json`). Τα πεδία είναι όλα τα πεδία του μοντέλου. Τα ξένα κλειδιά και τα many-to-many εμφανίζονται ως id (ή λίστα id). Τα αρχεία (FileField) εμφανίζονται ως URL. Η λήψη του αρχείου γίνεται με GET στο URL αυτό και ελέγχεται από τα δικαιώματα της εφαρμογής (`media_download`). Το ανέβασμα αρχείων μέσω του API δεν έχει δοκιμαστεί.

### Μοντέλα ανά ρόλο

`rw` = πλήρες CRUD, `ro` = μόνο ανάγνωση (POST/PUT/PATCH/DELETE επιστρέφουν 403).

**admin** — όλα: curricula, hrms, leaves, myprofile, phdapplications, phdstuds, projects, theses (42 μοντέλα· βλ. `registry.py::MODELS`).

**hr**

- `rw`: `hrms/application`, `hrms/decision`, `hrms/payrolldecision`, `hrms/reference`, `hrms/wageclass`, `hrms/rankclass`, `myprofile/employee`, `myprofile/staffmember`, `myprofile/adminstaff`, `myprofile/personalinfo`, `myprofile/admindepartment`
- `ro`: `curricula/institution`, `curricula/department`

**sec** (όλα περιορισμένα στο scope της γραμματείας)

- `rw`: `curricula/course`, `myprofile/student`, `myprofile/doctorateapplicant`, `leaves/leave`, `projects/project`, `theses/thesis`, όλα τα `phdapplications/*` (call, applicant, apppersonalinfo, application, degree, referenceletter, referencecontact, journalpublication, conferencepublication, workexperience) και όλα τα `phdstuds/*` (phdthesis, journalpublication, conferencepublication, teachingtask, examsupervision, administrativetask, thesisprogress, recommendation)
- `ro`: `curricula/institution`, `curricula/school`, `curricula/department`, `curricula/studyprogram`, `myprofile/staffmember`, `myprofile/associate`

Δεν εκθέτονται στο `sec/`: `PersonalInfo` (έχει ΑΦΜ/ΑΜΚΑ), `AdminStaff`, `AdminDepartment`, `Employee`, `CustomUserPermissions`, `Director` και τα μοντέλα hrms.

Η κατάσταση των πινάκων ορίζεται στο `registry.py` (`HR_ACCESS`, `SEC_ACCESS`), ώστε η προσθήκη ή αφαίρεση ενός μοντέλου να είναι μία ρητή αλλαγή.

## Αναζήτηση και σελιδοποίηση

Κάθε query param της λίστας, εκτός από τα `page`, `page_size`, `format`, `search`, `expand`, περνά ως φίλτρο στο Django `queryset.filter(...)`. Δηλαδή ισχύει όλη η σύνταξη των lookups (`__`):

```
GET /apiv2/hr/hrms/application/?employee=12
GET /apiv2/hr/hrms/application/?status=A&type=Fulltime
GET /apiv2/hr/hrms/application/?start_date__gte=2020-01-01&organization__icontains=πανεπιστ
GET /apiv2/hr/hrms/decision/?employee__faculty_staff__surname=Παπαδόπουλος
GET /apiv2/sec/myprofile/student/?program=21&surname__istartswith=Κ
```

Πολλά params συνδυάζονται με AND. Άγνωστο πεδίο ή μη έγκυρη τιμή επιστρέφει `400`.

Περιορισμοί για hr και sec (όχι για admin): το φίλτρο μπορεί να περάσει μέσω σχέσεων μόνο προς μοντέλα στα οποία έχει πρόσβαση ο ρόλος. Για παράδειγμα `?user__username=…` δεν επιτρέπεται (το `User` δεν είναι διαθέσιμο), και πεδία με όνομα `password`, `token`, `secret` δεν φιλτράρονται ποτέ. Φίλτρο στο ίδιο το ξένο κλειδί (π.χ. `?user=3`, `?employee=12`) επιτρέπεται.

Η απάντηση της λίστας είναι σελιδοποιημένη:

```json
{
  "count": 80,
  "next": "http://…/apiv2/hr/hrms/application/?page=2",
  "previous": null,
  "results": [ { "id": 1, … } ]
}
```

`page_size` (προεπιλογή 50, μέγιστο 500) και `page` ελέγχουν το μέγεθος και τη σελίδα.

## Αναζήτηση κειμένου (`search`)

`?search=<κείμενο>` ψάχνει σε πεδία ονομάτων και κειμένου του μοντέλου, χωρίς να χρειάζεται να γνωρίζετε τη διαδρομή του πεδίου. Οι λέξεις χωρίζονται με κενό και **όλες** πρέπει να ταιριάζουν (AND), η καθεμία σε κάποιο από τα πεδία (OR). Ισχύει μέχρι 6 λέξεις.

```
GET /apiv2/hr/myprofile/employee/?search=παπαδοπ
GET /apiv2/hr/hrms/application/?search=παπαδοπ πανεπιστ
GET /apiv2/sec/myprofile/student/?search=it2070
```

- Τα πεδία ορίζονται στο `registry.py` (`SEARCH_FIELDS`, `SEARCH_EXTRA`). Για μοντέλα που δεν αναφέρονται αναζητούνται όλα τα απλά πεδία κειμένου τους. Για τους εργαζομένους και για τα μοντέλα hrms αναζητούνται και το επώνυμο, το όνομα και το email του εργαζομένου.
- Συνδυάζεται με τα υπόλοιπα φίλτρα (`?search=…&status=A`) και στο `sec/` εφαρμόζεται μόνο μέσα στο scope.
- Περιορισμός: αγνοούνται τα πεζά/κεφαλαία, **όχι όμως οι τόνοι** («Παπαδοπουλος» δεν ταιριάζει με «Παπαδόπουλος»).

## Αναγνώσιμες τιμές: `display` και `expand`

Τα ξένα κλειδιά επιστρέφονται ως id. Για να μη χρειάζεται ένα επιπλέον αίτημα ανά id:

- Κάθε εγγραφή έχει πεδίο `display` (το `str()` του αντικειμένου, π.χ. `Μαρία Παπαδοπούλου (m@example.com)`), μόνο για ανάγνωση.
- `?expand=employee,decision` προσθέτει δίπλα στο id το `employee_display`, `decision_display` (λίστα για πεδία many-to-many). Επιτρέπονται μόνο ξένα κλειδιά προς μοντέλα στα οποία έχει πρόσβαση ο ρόλος, και αλλιώς επιστρέφεται `400`.

```
GET /apiv2/hr/hrms/application/?employee=12&expand=employee
```

## Υπολογιζόμενα endpoints hrms (hr και admin)

Μόνο ανάγνωση, με GET. Δίνουν τα νούμερα που δείχνει το UI του HR.

| URL | Περιεχόμενο |
|---|---|
| `/apiv2/hr/myprofile/employee/<pk>/summary/` | Στοιχεία εργαζομένου (ημερομηνία πρόσληψης, `wage_step_years`), τρέχων μισθολογικός κλιμάκιο και βαθμίδα με χρόνο σε αυτά (`wage_class`, `rank_class`), συμβάσεις ανά τύπο και κατάσταση, αποφάσεις αναγνώρισης με τα αποθηκευμένα `total_days` και χρόνο προϋπηρεσίας, μεταβολές (`payroll_decisions`) ανά τύπο |
| `/apiv2/hr/hrms/decision/<pk>/experience/` | `total_days`, `prior_days`, `all_days`, έτη/μήνες/ημέρες της απόφασης (`current`), των προηγούμενων (`prior`) και συνολικά (`all`), ημέρες ανά έτος (`by_year`), `overlaps` (διαστήματα όπου συμπίπτουν περισσότερες συμβάσεις, με τα id τους) και οι συμβάσεις που χρησιμοποιήθηκαν. Ισχύει η μέθοδος `calc_we_method` |

Το `summary` δεν γράφει τίποτα. Το `experience` **επανυπολογίζει και αποθηκεύει** το `total_days` της απόφασης, όπως κάνει η σελίδα υπολογισμού του UI (ο υπολογισμός είναι idempotent). Δεν υπάρχουν στο `sec/`.

## Scope της γραμματείας

Στο `sec/` οι εγγραφές περιορίζονται όπως και στο UI, με τα προγράμματα και τα τμήματα της `Secretariat` του χρήστη (`scopes.utils.get_secreteriat_scope` και ο `in_scope_of` των managers):

- Εγγραφή εκτός scope στη λίστα δεν εμφανίζεται, και σε GET/PUT/PATCH/DELETE με το `pk` της επιστρέφει `404`.
- Δημιουργία ή αλλαγή που θα έβγαζε την εγγραφή εκτός scope απορρίπτεται με `403` και δεν αποθηκεύεται τίποτα.
- Χρήστης χωρίς κανένα πρόγραμμα ή τμήμα στο scope παίρνει `403` σε όλο το `sec/`.

## Λογική του hrms

Οι εγγραφές μέσω API ακολουθούν τους ίδιους κανόνες με το UI, ώστε τα δεδομένα να μένουν συνεπή:

- **`hrms/application`** (σύμβαση): επικυρώνεται με τη φόρμα του τύπου της (`type`). Δηλαδή ισχύουν τα υποχρεωτικά πεδία ανά τύπο, δεν επιτρέπονται μελλοντικές ημερομηνίες, η έναρξη δεν μπορεί να είναι μετά τη λήξη ή μετά την πρόσληψη. Το `day_percentage` υπολογίζεται από το μοντέλο εκτός των τύπων `OT` και `External`, όπου δίνεται από εσάς ως δεκαδικός 0–1 (π.χ. `0.7` για 70%). Μετά από δημιουργία, αλλαγή ή διαγραφή επανυπολογίζονται οι αποφάσεις που περιλαμβάνουν τη σύμβαση και οι μεταγενέστερες του ίδιου εργαζομένου.
- **`hrms/decision`** (απόφαση αναγνώρισης): μετά την αποθήκευση τρέχει ο υπολογισμός (`calc()`), άρα το `total_days` ενημερώνεται αυτόματα.
- **`hrms/payrolldecision`**: για `decision_type = prior_service_recognition` τα στοιχεία (ημερομηνία, αριθμός πρωτοκόλλου, αρχείο, προϋπηρεσία) αντλούνται από τη συνδεδεμένη απόφαση (`linked_decision`).

Τύποι σύμβασης (`type`): `Fulltime`, `Workcontract`, `Teaching407fractioonal`, `Teachinghourly`, `Teachingdays`, `OT`, `External`. Κατάσταση (`status`): `P` (εκκρεμεί), `A` (εγκρίθηκε), `R` (δεν εγκρίθηκε). Είδος εργασίας (`work_type`): `Teaching`, `Research`.

Παράδειγμα δημιουργίας σύμβασης πλήρους απασχόλησης:

```bash
curl -X POST -H "Authorization: Token $TOKEN" -H "Content-Type: application/json" \
  http://localhost:30100/apiv2/hr/hrms/application/ \
  -d '{"employee": 12, "type": "Fulltime", "organization": "Πανεπιστήμιο Αθηνών",
       "start_date": "2010-09-01", "end_date": "2011-06-30",
       "status": "A", "work_type": "Teaching"}'
```

Σφάλματα επικύρωσης επιστρέφονται ως `400` με τη μορφή `{"πεδίο": ["μήνυμα"]}`.

## Κωδικοί απάντησης

| Κωδικός | Σημασία |
|---|---|
| 200 / 201 / 204 | Επιτυχία (ανάγνωση·αλλαγή / δημιουργία / διαγραφή) |
| 400 | Μη έγκυρο φίλτρο ή δεδομένα που απορρίφθηκαν από την επικύρωση |
| 401 | Λείπει ή είναι λάθος το token |
| 403 | Ο ρόλος δεν έχει πρόσβαση στο prefix, το μοντέλο είναι `ro`, ή η εγγραφή θα έβγαινε εκτός scope |
| 404 | Η εγγραφή δεν υπάρχει (ή είναι εκτός scope στο `sec/`) |

## Κώδικας

| Αρχείο | Ρόλος |
|---|---|
| `registry.py` | Ποια μοντέλα εκτίθενται ανά ρόλο, με επίπεδο πρόσβασης και κανόνες scope για τη γραμματεία |
| `urls.py` | Δημιουργεί έναν router ανά ρόλο |
| `views.py` | Γενικό `ModelViewSet`: queryset ανά ρόλο, φίλτρα, έλεγχος scope στις εγγραφές |
| `permissions.py` | `IsSuperUser`, `IsHrRole`, `IsSecretariatRole`, `IsReadOnly` |
| `serializers.py` | Γενικός `ModelSerializer` με όλα τα πεδία |
| `actions.py` | Τα υπολογιζόμενα endpoints `summary` και `experience` |
| `hooks.py` | Επικύρωση και επανυπολογισμοί του hrms (ρητές κλήσεις, χωρίς signals) |

Για να εκθέσετε νέο μοντέλο προσθέστε το στο `MODELS` (admin) και, αν χρειάζεται, στα `HR_ACCESS` ή `SEC_ACCESS`. Για το `sec/` ελέγξτε ότι ο manager του έχει σωστό `scope_filter`, αλλιώς προσθέστε κανόνα στο `SEC_SCOPE_OVERRIDES`.
