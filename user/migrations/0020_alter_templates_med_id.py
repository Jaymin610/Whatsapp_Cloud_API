# Generated by Django 4.1.2 on 2022-10-15 07:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0019_remove_developers_token_med_id_templates_med_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='templates',
            name='med_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
