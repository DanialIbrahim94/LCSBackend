# Generated by Django 4.1.6 on 2023-03-20 14:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0006_remove_coupons_used_alter_coupons_code'),
    ]

    operations = [
        migrations.DeleteModel(
            name='CompletedOrders',
        ),
    ]