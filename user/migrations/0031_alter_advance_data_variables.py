# Generated by Django 4.1.2 on 2022-11-05 10:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0030_alter_advance_data_recordid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='advance_data',
            name='variables',
            field=models.JSONField(blank=True, max_length=1000, null=True),
        ),
    ]