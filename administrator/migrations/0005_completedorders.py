# Generated by Django 4.1.6 on 2023-03-11 17:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0004_alter_coupons_options_rename_in_bulk_coupons_used'),
    ]

    operations = [
        migrations.CreateModel(
            name='CompletedOrders',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.IntegerField(verbose_name="Order's id")),
            ],
        ),
    ]
