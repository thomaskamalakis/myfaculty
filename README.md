# myfaculty

Εφαρμογή Django για τη διαχείριση των λειτουργιών ενός Τμήματος ΑΕΙ (αρχικά για το Τμήμα Πληροφορικής και Τηλεματικής του Χαροκοπείου Πανεπιστημίου): προφίλ προσωπικού και φοιτητών, πτυχιακές, διδακτορικές αιτήσεις και διδακτορικοί φοιτητές, άδειες, έργα, timesheets, παρουσίες, ανθρώπινο δυναμικό (HRMS) κ.ά.

Το repository είναι δημόσιο για εκπαιδευτική χρήση. **Δεν περιέχει κωδικούς, tokens ή πραγματικά δεδομένα**· όλα τα απαραίτητα για να το τρέξετε τοπικά ορίζονται από εσάς στο αρχείο `.env`.

## Τι χρειάζεστε

Για να τρέξει τοπικά (development):

| Απαίτηση | Σχόλιο |
|---|---|
| [Docker](https://docs.docker.com/get-docker/) και Docker Compose v2 | Τρέχουν όλα τα υπόλοιπα (Python, Postgres, Redis) |
| Git | Για το clone |

Δεν χρειάζεστε εγκατεστημένα Python ή Postgres στον υπολογιστή σας.

Τα παρακάτω είναι **προαιρετικά** και χρειάζονται μόνο αν θέλετε την αντίστοιχη λειτουργία:

| Λειτουργία | Τι χρειάζεται | Χωρίς αυτό |
|---|---|---|
| Αποστολή e-mail (Gmail) | Λογαριασμός Gmail και Google Cloud project με Gmail API (βλ. παρακάτω) | Με `DUMMY_EMAILS=True` τα μηνύματα τυπώνονται στο log του `web`/`worker` |
| reCAPTCHA σε παραγωγή | Δικό σας ζεύγος κλειδιών reCAPTCHA v2 | Στο `env.template` υπάρχουν τα δημόσια *test* κλειδιά της Google που δουλεύουν τοπικά |
| LDAP login | LDAP server και λογαριασμός bind | Χωρίς `AUTH_LDAP_SERVER_URI` χρησιμοποιούνται μόνο τοπικοί λογαριασμοί Django |
| Συγχρονισμός με το SIS (Keycloak) | Στοιχεία πρόσβασης στο SIS | Οι σχετικές λειτουργίες απλά δεν χρησιμοποιούνται |
| Budibase | `BUDI_KEY` | Δεν χρειάζεται για τη λειτουργία της εφαρμογής |

## Εγκατάσταση και εκτέλεση

1. Κατεβάστε τον κώδικα:
   ```
   git clone <url-του-repository>
   cd <φάκελος-του-repository>
   ```

2. Δημιουργήστε το αρχείο `.env` από το template και διορθώστε τουλάχιστον τα `SECRET_KEY` και `POSTGRES_PASSWORD`:
   ```
   cp env.template .env
   ```
   Μπορείτε να φτιάξετε `SECRET_KEY` με:
   ```
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   ```
   Το `.env` δεν πρέπει να ανεβαίνει ποτέ στο git (είναι ήδη στο `.gitignore`).

3. Χτίστε και ξεκινήστε τα containers:
   ```
   docker compose build
   docker compose up -d
   ```

4. Δημιουργήστε τη βάση (τα migrations περιλαμβάνονται στο repository, **δεν** χρειάζεται `makemigrations`):
   ```
   docker compose exec web python manage.py migrate
   ```

5. Δημιουργήστε διαχειριστή:
   ```
   docker compose exec web python manage.py createsuperuser
   ```

6. (Προαιρετικά) Φορτώστε δοκιμαστικά δεδομένα — ίδρυμα, σχολή, τμήμα, προγράμματα σπουδών, τρία δοκιμαστικά μέλη ΔΕΠ και γραμματείες:
   ```
   docker compose exec web python manage.py runscript initial_data
   ```
   Οι δοκιμαστικοί χρήστες έχουν κωδικό `test1234` (π.χ. `ng`, `pg`, `undsec`, `csisec`) και διευθύνσεις της μορφής `ng@example.com`. Το username προκύπτει από το τμήμα της διεύθυνσης πριν το `@`. Είναι για development μόνο· ο κωδικός είναι γνωστός σε όλους, μην το κάνετε ποτέ σε πραγματικό server.

7. (Προαιρετικά) Μεταγλωττίστε τα μηνύματα για τη διγλωσσία:
   ```
   docker compose exec web django-admin compilemessages
   ```

Η εφαρμογή τρέχει στο <http://localhost:30100> και το admin site στο <http://localhost:30100/admin>.

Τα logs (και τα e-mail όταν `DUMMY_EMAILS=True`, π.χ. οι σύνδεσμοι ενεργοποίησης λογαριασμού) φαίνονται με:
```
docker compose logs -f web worker
```

Για να σταματήσετε τα containers: `docker compose down` (τα δεδομένα της βάσης μένουν στο φάκελο `data/`, που δεν ανεβαίνει στο git).

## Ρυθμίσεις (`.env`)

| Μεταβλητή | Περιγραφή |
|---|---|
| `SECRET_KEY` | Μυστικό κλειδί του Django |
| `DEBUG` | `True` για development. Σε παραγωγή πάντα `False` |
| `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS` | Λίστες χωρισμένες με κόμμα (host names / origins του server σας) |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` | Στοιχεία της βάσης |
| `DUMMY_EMAILS` | `True`: τα e-mail τυπώνονται στο log. `False`: αποστέλλονται μέσω Gmail API |
| `DEAN_EMAIL`, `ALWAYS_NOTIFY`, `EMAIL_PLATFORM_URL` | Διευθύνσεις και URL που χρησιμοποιούνται στις ειδοποιήσεις |
| `RECAPTCHA_PUBLIC_KEY`, `RECAPTCHA_PRIVATE_KEY` | Κλειδιά reCAPTCHA v2 |
| `AUTH_LDAP_*` | Προαιρετικό LDAP login (βλ. παρακάτω) |
| `SIS_*`, `BUDI_KEY` | Προαιρετικοί συγχρονισμοί |

### Αποστολή e-mail μέσω Gmail (προαιρετικό)

Με `DUMMY_EMAILS=False` η εφαρμογή στέλνει e-mail με το Gmail API (`code/myfaculty/mailer/gmail.py`). Χρειάζεται:

1. Ένα project στο [Google Cloud Console](https://console.cloud.google.com/) με ενεργοποιημένο το **Gmail API**.
2. Ένα **OAuth client ID** τύπου *Desktop app* (και OAuth consent screen με τον λογαριασμό σας ως test user).
3. Κατεβάστε το JSON των client secrets και αποθηκεύστε το ως `code/myfaculty/mailer/auth/no-reply-gmail.json`.
4. Στην πρώτη αποστολή η εφαρμογή ανοίγει τη ροή εξουσιοδότησης της Google και δημιουργεί το `code/myfaculty/mailer/auth/no-reply-token.json`. Επειδή η εφαρμογή τρέχει μέσα σε container, είναι πιο εύκολο να δημιουργήσετε το token μία φορά σε δικό σας μηχάνημα με Python (`google-auth-oauthlib`, scope `https://mail.google.com/`) και να αντιγράψετε το αρχείο στον ίδιο φάκελο.
5. Τα δύο αυτά αρχεία **δεν πρέπει ποτέ να μπουν στο git** (το `.gitignore` τα αγνοεί). Αν διαρρεύσουν, ανακαλέστε το token και δημιουργήστε νέο client secret.

Ο αποστολέας είναι ο `no-reply@example.com` (παράμετρος `from_ad` στο `gmail.py`)· αλλάξτε τον ώστε να ταιριάζει με το δικό σας λογαριασμό.

### LDAP (προαιρετικό)

Αν ορίσετε `AUTH_LDAP_SERVER_URI`, οι χρήστες με το domain του ιδρύματος (`INTERNAL_DOMAIN` στο `settings.py`, προεπιλογή `example.com`) ελέγχονται στον LDAP server. Το `AUTH_LDAP_BIND_DN` είναι ο λογαριασμός με τον οποίο γίνεται η αναζήτηση και το `AUTH_LDAP_BIND_PASSWORD` ο κωδικός του. Το search base (`dc=example,dc=com`) και τα attributes ορίζονται στο `myfaculty/settings.py`. Αν δεν ορίσετε LDAP, συνδέεστε με τους τοπικούς λογαριασμούς που φτιάχνετε εσείς (`createsuperuser`, admin site ή εγγραφή χρήστη).

### Placeholders (`example.com`)

Για τη δημοσίευση του repository, όλες οι διευθύνσεις e-mail και τα hostnames του αρχικού ιδρύματος αντικαταστάθηκαν με `example.com`. Πριν τρέξετε την εφαρμογή για το δικό σας ίδρυμα, αντικαταστήστε τα με τα δικά σας:

| Τι | Πού | Τιμή στο repository |
|---|---|---|
| Domain του ιδρύματος (`INTERNAL_DOMAIN`) | `myfaculty/settings.py` | `example.com` |
| LDAP search base | `myfaculty/settings.py` (`AUTH_LDAP_USER_SEARCH`) | `dc=example,dc=com` |
| Αποστολέας e-mail | `mailer/gmail.py` (`from_ad`) | `no-reply@example.com` |
| Δοκιμαστικά μέλη ΔΕΠ και γραμματείες | `scripts/initial_data.py` | `*@example.com` (το `get_or_create_user` ελέγχει το `@example.com`, αλλάξτε το μαζί με το `INTERNAL_DOMAIN`) |
| Σύνδεσμος επαναφοράς κωδικού | `myprofile/templates/myprofile/password_reset_choice.html` | `https://accounts.example.com` |
| Σύνδεσμος αναφοράς προβλημάτων | `myprofile/templates/registration/base2.html` | `https://tickets.example.com` |
| API του SIS | `sis/sis.py` | `https://api.sis.example.com` |
| Email κοσμήτορα | `.env` (`DEAN_EMAIL`) | `dean@example.com` |

Τα `INTERNAL_DOMAIN` και τα δοκιμαστικά e-mail πρέπει να ταιριάζουν, αλλιώς οι έλεγχοι «εσωτερικού» χρήστη (login, εγγραφή, επαναφορά κωδικού) δεν θα δουλεύουν σωστά.

## Δομή

```
code/myfaculty/        Django project
  myfaculty/           settings, urls, custom authentication backend
  myprofile/           χρήστες, προσωπικό, φοιτητές
  curricula/, scopes/  ίδρυμα/τμήματα/προγράμματα και δικαιώματα γραμματείας
  theses/, phdapplications/, phdstuds/   πτυχιακές και διδακτορικά
  leaves/, projects/, timesheets/, attendances/, rfs/, associates/
  hrms/                ανθρώπινο δυναμικό: συμβάσεις, αποφάσεις προϋπηρεσίας
  mailer/              αποστολή e-mail (Gmail API, Celery)
  api/, apiv2/         REST API (η τεκμηρίωση του apiv2 στο apiv2/README.md)
  mcp_server/          MCP server πάνω από το apiv2 (MCP_MODE στο .env)
  scripts/             δοκιμαστικά δεδομένα (initial_data.py)
Dockerfile, docker-compose.yaml, env.template
```

## Tests

```
docker compose exec web python manage.py test
```

## Σημειώσεις ασφαλείας

- Μην ανεβάζετε στο git: `.env`, τα αρχεία στο `mailer/auth/`, dumps της βάσης, αρχεία στο `media/` ή οτιδήποτε με προσωπικά δεδομένα.
- Το compose αρχείο είναι για development (`runserver`, `DEBUG=True`). Για παραγωγή χρειάζονται gunicorn, reverse proxy με TLS, `DEBUG=False`, δικό σας `SECRET_KEY` και `collectstatic`· τα αρχεία του φακέλου `media/` πρέπει να σερβίρονται μόνο μέσω της εφαρμογής (`media_download`), όχι ως στατικά αρχεία.

## Άδεια

MIT — βλ. το αρχείο [LICENSE](LICENSE).
