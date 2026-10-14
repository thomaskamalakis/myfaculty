INFORM_ASSIGNMENT_TITLE = "Ανάθεση Διπλωματικής / Thesis Assignment"
INFORM_ASSIGNMENT_BODY = """
<title>Ενημέρωση Ανάθεσης Διπλωματικής / Thesis Assignment Notification</title>
</head>

<body style="font-family: Arial, sans-serif; line-height: 1.6; color: #222;">

<div style="max-width: 600px; margin: auto; padding: 20px;">

<!-- Greek Section -->
<h2 style="color:#2c3e50;">Ανάθεση Διπλωματικής Εργασίας</h2>

<p>
Σας ενημερώνουμε ότι σας έχει ανατεθεί μέσω του συστήματος παρακολούθησης διπλωματικών μία διπλωματική εργασία με τα παρακάτω στοιχεία
</p>

<p>
<strong>Τίτλος:</strong> {title_gr} <br>
<strong>Επιβλέπων:</strong> {supervisor} <br>
</p>

<p>
Θα πρέπει να συνδεθείτε στο σύστημα και να αποδεχθείτε την ανάθεση
</p>

<table cellpadding="0" cellspacing="0" style="margin:20px 0;">
  <tr>
    <td align="center" style="background:#1a73e8; padding:12px 22px; border-radius:4px;">
      <a href="{url}" style="color:white; text-decoration:none; font-weight:bold;">
        Συνδεθείτε
      </a>
    </td>
  </tr>
</table>

<hr style="margin-top:30px; margin-bottom:30px;">

<!-- English Section -->
<h2 style="color:#2c3e50;">Thesis Assignment</h2>

<p>
You are hereby informed that a thesis has been assigned to you through the thesis management system with the following details:
</p>

<p>
<strong>Title:</strong> {title_en} <br>
<strong>Supervisor:</strong> {supervisor} <br>
</p>

<p>
You are required to log in to the system and accept the assignment.
</p>

<table cellpadding="0" cellspacing="0" style="margin:20px 0;">
  <tr>
    <td align="center" style="background:#1a73e8; padding:12px 22px; border-radius:4px;">
      <a href="{url}" style="color:white; text-decoration:none; font-weight:bold;">
        Log in
      </a>
    </td>
  </tr>
</table>

<hr style="margin-top:30px; margin-bottom:30px;">

</div>
</body>
"""