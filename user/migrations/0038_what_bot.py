# Generated by Django 4.1.2 on 2022-11-12 09:59

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('user', '0037_advance_data_text'),
    ]

    operations = [
        migrations.CreateModel(
            name='What_Bot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bot_name', models.CharField(max_length=100, null=True)),
                ('is_on', models.BooleanField(default=0)),
                ('message_pair', models.JSONField()),
                ('provider', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user.wa_msg_provider')),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='user.user1')),
            ],
        ),
    ]
