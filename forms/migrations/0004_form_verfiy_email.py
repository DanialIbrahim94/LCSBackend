# Generated by Django 4.1.6 on 2024-05-05 23:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0003_remove_form_agreed_alter_field_identifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='verfiy_email',
            field=models.BooleanField(default=False),
        ),
    ]