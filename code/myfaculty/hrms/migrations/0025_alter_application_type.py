from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hrms', '0024_payrolldecision_term_end_date'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='type',
            field=models.CharField(choices=[('Fulltime', 'Πλήρους Απασχόλησης'), ('Workcontract', 'Σύμβαση Έργου'), ('Teaching407fractioonal', 'Διδασκαλία με ανάθεση συμφ. με το 407/80 με έκτα'), ('Teachinghourly', 'Διδασκαλία (υπολογισμός με ώρες διδασκαλίας)'), ('Teachingdays', 'Διδασκαλία (υπολογισμός με ημέρες διδασκαλίας)'), ('OT', 'Άλλος Τύπος'), ('External', 'Εμπειρία Εξωτερικού')], max_length=200, null=True),
        ),
    ]
