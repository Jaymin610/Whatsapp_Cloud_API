# Generated by Django 4.1.2 on 2022-12-12 10:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0059_sms_outbox'),
    ]

    operations = [
        migrations.AlterField(
            model_name='new_templates',
            name='text_msg',
            field=models.TextField(blank=True, null=True),
        ),
    ]
