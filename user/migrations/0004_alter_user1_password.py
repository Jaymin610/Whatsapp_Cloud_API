# Generated by Django 4.0.6 on 2022-10-10 07:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0003_alter_messagelog_reply_number_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user1',
            name='password',
            field=models.CharField(blank=True, max_length=25, null=True),
        ),
    ]
