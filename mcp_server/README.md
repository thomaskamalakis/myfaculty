# myfaculty MCP server

Server [MCP](https://modelcontextprotocol.io) που εκθέτει το REST API του `apiv2` ως tools σε LLM clients (Claude Code, Claude Desktop κ.ά.). Δεν κρατά μυστικά και δεν υλοποιεί δικαιώματα: ο client στέλνει το δικό του Django API token και ο server το προωθεί αυτούσιο στο Django, που αποφασίζει τι επιτρέπεται (HR / γραμματεία με scope / admin). Βλ. `code/myfaculty/apiv2/README.md`.

Transport: streamable HTTP, endpoint `/mcp`, θύρα `8765`.

## Tools

Τα περισσότερα παίρνουν `role`: `hr`, `sec` ή `admin` (το token του χρήστη καθορίζει ποιοι ρόλοι δουλεύουν, οι υπόλοιποι απαντούν 403).

| Tool | Τι κάνει |
|---|---|
| `list_resources(role)` | Ποιοι πόροι (`app/model`) υπάρχουν για τον ρόλο |
| `describe_resource(role, resource)` | Πεδία, τύποι, υποχρεωτικά και choices (OPTIONS του API) |
| `search(role, resource, search, filters, expand, page, page_size)` | Αναζήτηση: `search` για ελεύθερο κείμενο (όνομα, email, αριθμοί), `filters` με Django lookups, π.χ. `{"employee": 12, "start_date__gte": "2020-01-01"}`, `expand` π.χ. `["employee"]` για αναγνώσιμο `employee_display` |
| `get(role, resource, id)` | Μία εγγραφή |
| `employee_summary(employee_id, role)` | Σύνοψη εργαζομένου (HR): ΜΚ, βαθμίδα, συμβάσεις, αποφάσεις, μεταβολές |
| `decision_experience(decision_id, role)` | Υπολογισμός προϋπηρεσίας απόφασης (HR): ημέρες, έτη/μήνες/ημέρες, ανά έτος, επικαλύψεις. Επανυπολογίζει και αποθηκεύει το `total_days` |
| `create(role, resource, data)` | Δημιουργία |
| `update(role, resource, id, data)` | Μερική ενημέρωση (PATCH) |
| `delete(role, resource, id)` | Διαγραφή (μη αναστρέψιμη) |

Τα `create`, `update`, `delete` δηλώνουν στο MCP ότι δεν είναι read-only, ώστε οι clients να ζητούν επιβεβαίωση.

## Λειτουργία (`MCP_MODE`)

Ο διακόπτης ορίζεται στο `.env` (βλ. `env.template`) και ισχύει για ολόκληρο τον server:

| `MCP_MODE` | Τι επιτρέπεται |
|---|---|
| `OFF` (προεπιλογή) | Ο server ξεκινά και ο client βλέπει τα tools, αλλά κάθε κλήση επιστρέφει μήνυμα ότι ο MCP είναι απενεργοποιημένος και δεν φτάνει τίποτα στο API |
| `READ_ONLY` | Ανάγνωση και αναζήτηση: `list_resources`, `describe_resource`, `search`, `get`, `employee_summary`, `decision_experience`. Τα `create`, `update`, `delete` επιστρέφουν μήνυμα ότι δεν επιτρέπονται |
| `FULL` | Επιτρέπονται όλα |

- Άγνωστη ή κενή τιμή λογίζεται ως `OFF` (και γράφεται προειδοποίηση στο log).
- Η αλλαγή του `.env` ισχύει μετά από επανεκκίνηση του container: `docker compose up -d mcp`.
- Το `decision_experience` επιτρέπεται και στο `READ_ONLY`: ανανεώνει μόνο το παραγόμενο `total_days` της απόφασης και δεν αλλάζει δεδομένα του χρήστη.
- Ο διακόπτης δεν είναι ανά χρήστη. Τα δικαιώματα κάθε token (ρόλος και scope) τα επιβάλλει πάντα το Django.

## Τι χρειάζεται

1. **Token στο Django** για κάθε άνθρωπο ή client που θα συνδέεται. Ο χρήστης πρέπει να είναι `HrStaff` (για `hr`) ή να έχει `Secretariat` με προγράμματα/τμήματα (για `sec`):
   ```
   docker compose exec web python manage.py drf_create_token <username>
   ```
2. **Το container** (στο `docker-compose.yaml` υπάρχει ήδη το service `mcp`):
   ```
   docker compose up -d --build mcp web
   ```
   Στο dev ακούει μόνο στο `127.0.0.1:8765`.
3. **Σύνδεση client**, π.χ. Claude Code:
   ```
   claude mcp add --transport http myfaculty http://localhost:8765/mcp --header "Authorization: Token <token>"
   ```
   Ή στο `.mcp.json` / config του client:
   ```json
   {
     "mcpServers": {
       "myfaculty": {
         "type": "http",
         "url": "http://localhost:8765/mcp",
         "headers": { "Authorization": "Token <token>" }
       }
     }
   }
   ```

## Ρυθμίσεις (environment του container)

| Μεταβλητή | Προεπιλογή | Σχόλιο |
|---|---|---|
| `MYFACULTY_API_URL` | `http://web:8000` | Πού βρίσκεται το Django (εσωτερικό δίκτυο) |
| `MYFACULTY_API_HOST` | `localhost` | Η τιμή του `Host` header προς το Django. Πρέπει να υπάρχει στο `ALLOWED_HOSTS` (το όνομα `web` του compose δεν υπάρχει) |
| `MYFACULTY_API_TIMEOUT` | `30` | Timeout σε δευτερόλεπτα |
| `MCP_HOST`, `MCP_PORT` | `0.0.0.0`, `8765` | Πού ακούει ο MCP server |
| `MCP_MODE` | `OFF` | `OFF`, `READ_ONLY` ή `FULL` (βλ. παραπάνω) |

## Παραγωγή

Στο `docker-compose-prod.yaml` το service `mcp` δεν δημοσιεύει θύρα· το `nginx/nginx.conf` το προωθεί στο `https://<host>:30100/mcp` (TLS από το nginx). Ορίστε `MCP_API_HOST` στο `.env` αν θέλετε άλλο `Host` από `localhost` προς το Django (π.χ. το public hostname).

Σημειώσεις ασφαλείας:

- Ο MCP server δεν ελέγχει το token· τον ρόλο και το scope τα επιβάλλει το Django. Ένα token ισχύει όσο ο χρήστης του έχει δικαιώματα. Για ανάκληση διαγράψτε το token στο admin (Auth Token → Tokens).
- Χωρίς TLS τα tokens ταξιδεύουν ως απλό κείμενο: μην ανοίξετε τη θύρα `8765` εκτός localhost, χρησιμοποιήστε το nginx.
- Δώστε σε κάθε client token χρήστη με τα ελάχιστα δικαιώματα (π.χ. χρήστης γραμματείας για χρήση που αφορά μόνο φοιτητές).

## Τοπική δοκιμή χωρίς Docker

```
cd mcp_server
pip install -r requirements.txt
MYFACULTY_API_URL=http://localhost:30100 python server.py
```
