# Generated by Django 4.1.2 on 2022-12-19 11:08

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0066_alter_messagelog_received_msg_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Message_History',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(blank=True, null=True)),
                ('time', models.DateTimeField(auto_now_add=True)),
                ('msg_type', models.TextField(null=True)),
                ('customer_number', models.CharField(max_length=15)),
                ('status', models.CharField(max_length=10, null=True)),
                ('provider', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user.wa_msg_provider')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user.user1')),
            ],
        ),
    ]
