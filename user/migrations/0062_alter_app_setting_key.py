# Generated by Django 4.1.2 on 2022-12-13 06:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0061_app_setting'),
    ]

    operations = [
        migrations.AlterField(
            model_name='app_setting',
            name='key',
            field=models.CharField(max_length=100, null=True, unique=True),
        ),
    ]
