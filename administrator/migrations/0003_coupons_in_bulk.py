# Generated by Django 4.1.6 on 2023-03-11 11:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0002_user_last_recharge_request'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupons',
            name='in_bulk',
            field=models.BooleanField(default=False),
        ),
    ]
