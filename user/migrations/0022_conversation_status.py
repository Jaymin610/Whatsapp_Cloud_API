# Generated by Django 4.1.2 on 2022-10-15 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0021_data_summary_what_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='Conversation_Status',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('to', models.CharField(max_length=15, null=True)),
                ('provider', models.CharField(max_length=15, null=True)),
                ('inbox_msg', models.CharField(blank=True, max_length=255, null=True)),
                ('template', models.CharField(blank=True, max_length=100, null=True)),
                ('send_time', models.DateTimeField()),
                ('received_time', models.DateTimeField(null=True)),
                ('conversation_status', models.CharField(default='Pending', max_length=100)),
            ],
        ),
    ]
