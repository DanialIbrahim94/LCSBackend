# Generated by Django 4.1.6 on 2023-03-11 13:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0003_coupons_in_bulk'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='coupons',
            options={'verbose_name': 'Coupons', 'verbose_name_plural': 'Coupons'},
        ),
        migrations.RenameField(
            model_name='coupons',
            old_name='in_bulk',
            new_name='used',
        ),
    ]