# Generated by Django 4.1.2 on 2022-12-19 12:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0067_message_history'),
    ]

    operations = [
        migrations.AddField(
            model_name='message_history',
            name='api_number',
            field=models.CharField(max_length=15, null=True),
        ),
        migrations.AlterField(
            model_name='message_history',
            name='customer_number',
            field=models.CharField(max_length=15, null=True),
        ),
    ]
