# Generated by Django 4.1.2 on 2022-10-15 06:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0018_templates_temp_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='developers_token',
            name='med_id',
        ),
        migrations.AddField(
            model_name='templates',
            name='med_id',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
        migrations.AddField(
            model_name='templates',
            name='status',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
