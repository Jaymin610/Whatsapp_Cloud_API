# Generated by Django 4.1.2 on 2023-01-03 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0088_staff'),
    ]

    operations = [
        migrations.AddField(
            model_name='user1',
            name='staff_name',
            field=models.CharField(blank=True, max_length=32, null=True),
        ),
    ]
