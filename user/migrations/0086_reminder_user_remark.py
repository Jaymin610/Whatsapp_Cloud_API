# Generated by Django 4.1.2 on 2022-12-26 12:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0085_reminder_user_a_msg_id_reminder_user_a_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='reminder_user',
            name='remark',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
