# Generated by Django 4.1.2 on 2022-10-13 06:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0014_remove_messagelog_msg_status_templates'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Templates',
        ),
    ]
