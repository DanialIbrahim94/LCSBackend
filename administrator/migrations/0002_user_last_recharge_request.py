# Generated by Django 4.1.6 on 2023-03-10 11:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='last_recharge_request',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
