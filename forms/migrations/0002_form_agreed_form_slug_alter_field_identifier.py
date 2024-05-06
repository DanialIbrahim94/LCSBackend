# Generated by Django 4.1.6 on 2024-05-05 15:09

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('forms', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='form',
            name='agreed',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='form',
            name='slug',
            field=models.SlugField(default=uuid.uuid4, unique=True),
        ),
        migrations.AlterField(
            model_name='field',
            name='identifier',
            field=models.CharField(choices=[('text input', 'control_input'), ('email input', 'control_email'), ('phone input', 'control_phone'), ('datetime input', 'control_datetime'), ('dropdown input', 'control_dropdown')], max_length=20),
        ),
    ]