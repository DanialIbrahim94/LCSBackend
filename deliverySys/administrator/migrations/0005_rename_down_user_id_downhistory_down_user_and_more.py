# Generated by Django 4.1.6 on 2023-02-07 19:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0004_downhistory'),
    ]

    operations = [
        migrations.RenameField(
            model_name='downhistory',
            old_name='down_user_id',
            new_name='down_user',
        ),
        migrations.RenameField(
            model_name='downhistory',
            old_name='from_user_id',
            new_name='from_user',
        ),
    ]
