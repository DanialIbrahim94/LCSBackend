# Generated by Django 4.1.6 on 2023-04-15 08:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('administrator', '0008_user_jotform_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='jotform_id',
            field=models.TextField(default=None, max_length=30, null=True),
        ),
    ]
