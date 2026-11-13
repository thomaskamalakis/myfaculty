# Sign in with Google

Η Google προσφέρεται ως **εναλλακτικός** τρόπος login για εσωτερικούς (@example.com, Google Workspace) και εξωτερικούς χρήστες. Δεν καταργείται κανένας υπάρχων τρόπος: LDAP, email+κωδικός, εγγραφή με token και reset κωδικού μένουν ως έχουν.

## Τι έχουμε κάνει

- **django-allauth** (μόνο `socialaccount` + πάροχος Google). Δεν εκτίθεται το `allauth.urls`, ώστε να μη σκιάσει το `django.contrib.auth.urls`.
- **Adapter** `code/myfaculty/myfaculty/socialadapter.py` (`GoogleAdapter`):
  - δέχεται μόνο email που η Google έχει επαληθεύσει (άρα δεν χρειάζεται δικό μας verification για τους εξωτερικούς)
  - συνδέει με υπάρχοντα χρήστη βάσει email ή username (σχήμα του `create_user_if_required`: local-part για @example.com, ολόκληρο το email για εξωτερικούς), χωρίς διπλούς χρήστες
  - απορρίπτει ανενεργούς λογαριασμούς και emails που ταιριάζουν σε πάνω από έναν χρήστη
  - οι νέοι χρήστες δημιουργούνται με unusable password
- **Login page**: κουμπί «Σύνδεση με Google» (`registration/login.html`), ορατό μόνο αν υπάρχουν τα credentials (context processor `myprofile/context_processors.py`).
- **URLs** της Google εκτός `i18n_patterns`, με σταθερό redirect URI `/accounts/google/login/callback/`.
- **Settings**: `SITE_ID`, apps/middleware/backend του allauth (ο backend μπήκε τελευταίος), `SOCIALACCOUNT_*`. Τα credentials διαβάζονται από env: `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_SECRET`.
- **Env/compose**: οι δύο μεταβλητές προστέθηκαν στα `docker-compose.yaml`, `docker-compose-prod.yaml` (web και worker) και στο `env.template`.
- **Dependencies**: `django-allauth[socialaccount]` στο `requirements.txt`.
- **Μεταφράσεις**: νέα strings στο `locale/en` (`.po` και `.mo`).

Δεν έχει δοκιμαστεί πραγματικό login με Google, γιατί δεν υπάρχουν ακόμη credentials.

## Privacy Policy και Terms of Service (για το OAuth consent screen)

- Δημόσιες σελίδες χωρίς login: **`/privacy/`** και **`/terms/`** (εκτός `i18n_patterns`, σταθερά URLs). Δίγλωσσες· η γλώσσα ακολουθεί session/browser ή το `?lang=el|en`.
- Κώδικας: `myprofile/legal.py`, templates στο `myprofile/templates/legal/`, URLs στο `myfaculty/urls.py`. Links στο login και στην εγγραφή.
- Η `/privacy/` **δεν αντιγράφει** την πολιτική του Πανεπιστημίου, παραπέμπει σε αυτήν (https://www.example.com/gdpr/ και το PDF της Πολιτικής Απορρήτου) και προσθέτει ό,τι αφορά την εφαρμογή: Google login (μόνο όνομα, email, επαλήθευση email), cookies (μόνο απαραίτητα), logs, δικαιώματα και DPO `dpo@example.com`. Επικοινωνία για τεχνικά θέματα: `admin@example.com`.
- Στα κείμενα δεν μπήκαν τηλέφωνο και διεύθυνση του DPO.
- **Τα κείμενα είναι πρόχειρα και πρέπει να τα εγκρίνει ο DPO του Πανεπιστημίου** πριν δοθούν στη Google.

## Τι πρέπει να κάνουμε

1. **Google Cloud Console**: OAuth client ID τύπου Web, consent screen **External** (και publish, ώστε να μην εμφανίζεται «unverified app»). Redirect URIs:
   - `https://myfaculty-dev.example.com/accounts/google/login/callback/`
   - `https://myfaculty.example.com/accounts/google/login/callback/` (prod, αργότερα)
   - Στο consent screen: Application home page = το domain της εφαρμογής, Privacy policy link = `https://<domain>/privacy/`, Terms of service link = `https://<domain>/terms/`. Το domain πρέπει να προστεθεί και στα Authorized domains.
2. **Deploy στο dev**:
   ```
   git fetch && git checkout google-login
   # στο .env: GOOGLE_OAUTH_CLIENT_ID="..." και GOOGLE_OAUTH_SECRET="..."
   docker compose build          # άλλαξε το requirements.txt
   docker compose up -d
   docker compose exec web python manage.py migrate   # πίνακες allauth και sites
   ```
   Το `compilemessages` δεν χρειάζεται, το `.mo` είναι στο commit.
3. **Δοκιμές στο dev**:
   - login με @example.com (υπάρχων χρήστης LDAP)
   - login με υπάρχοντα εξωτερικό χρήστη
   - login με νέο gmail (δημιουργία χρήστη)
   - regression: LDAP login, email+κωδικός, εγγραφή με token, reset κωδικού, API με DRF token
4. **Merge** στο `master` μετά την επιτυχή δοκιμή, και μετά deploy στο prod με τα ίδια βήματα και τα prod credentials.
5. Έλεγχος των κειμένων `/privacy/` και `/terms/` από τον DPO (και επιβεβαίωση του σωστού τηλεφώνου/διεύθυνσης, αν θέλετε να μπουν).
6. Προαιρετικά: κουμπί «Εγγραφή με Google» και στη σελίδα register.

## Γνωστά σημεία

- Εξωτερικοί χωρίς λογαριασμό Google (π.χ. Outlook, Yahoo) συνεχίζουν να χρησιμοποιούν την παλιά ροή εγγραφής.
- Το `makemigrations --check` δείχνει εκκρεμή migration στο `timesheets` (`0017_alter_timesheet_month`). Είναι προϋπάρχουσα και άσχετη με αυτή την αλλαγή.
- Όσο λείπουν τα credentials, το κουμπί κρύβεται και η εφαρμογή λειτουργεί όπως πριν.
