# Generated manually to switch the upload_to callable from
# myprofile.directories.we_dir to myprofile.directories.hrms_dir following the
# workexperience -> hrms app rename. State-only change (upload_to is a Python
# attribute, not a DB column), no real DDL. New uploads land under
# hrms/documents/... ; files already stored under workexperience/documents/...
# are unaffected (see myprofile/checks.py can_download()).

import myprofile.directories
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hrms', '0012_alter_decision_total_days'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='related_document1',
            field=models.FileField(blank=True, help_text='To αρχείο της σύμβασης', null=True, upload_to=myprofile.directories.hrms_dir),
        ),
        migrations.AlterField(
            model_name='application',
            name='related_document2',
            field=models.FileField(blank=True, help_text='Το αρχείο της βεβαίωσης', null=True, upload_to=myprofile.directories.hrms_dir),
        ),
        migrations.AlterField(
            model_name='decision',
            name='document',
            field=models.FileField(blank=True, help_text='Απόφαση', null=True, upload_to=myprofile.directories.hrms_dir),
        ),
    ]
