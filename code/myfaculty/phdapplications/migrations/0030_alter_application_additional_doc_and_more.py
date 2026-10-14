import core.validators
import myprofile.directories
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('phdapplications', '0029_alter_application_additional_doc_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='additional_doc',
            field=models.FileField(blank=True, max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='application',
            name='cv',
            field=models.FileField(blank=True, max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='application',
            name='declaration_not_enlisted',
            field=models.FileField(max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='application',
            name='doctoral_plan',
            field=models.FileField(max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='application',
            name='id_document',
            field=models.FileField(max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='application',
            name='proof_english',
            field=models.FileField(blank=True, max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='conferencepublication',
            name='pdf',
            field=models.FileField(max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='degree',
            name='degree',
            field=models.FileField(max_length=1000, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='degree',
            name='transcript_of_records',
            field=models.FileField(blank=True, max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='journalpublication',
            name='pdf',
            field=models.FileField(max_length=1000, null=True, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='referenceletter',
            name='letter',
            field=models.FileField(max_length=1000, upload_to=myprofile.directories.phdapp_ref_dir, validators=[core.validators.validate_pdf_file]),
        ),
        migrations.AlterField(
            model_name='workexperience',
            name='contract',
            field=models.FileField(max_length=1000, upload_to=myprofile.directories.phdapp_dir, validators=[core.validators.validate_pdf_file]),
        ),
    ]
