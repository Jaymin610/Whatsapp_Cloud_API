# Generated by Django 4.1.2 on 2022-11-26 12:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0047_rename_new_templtes_new_templates'),
    ]

    operations = [
        migrations.AddField(
            model_name='outbox',
            name='variables',
            field=models.CharField(max_length=500, null=True),
        ),
    ]
