# Generated by Django 4.1.2 on 2022-10-15 07:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0020_alter_templates_med_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='data_summary',
            name='what_status',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
