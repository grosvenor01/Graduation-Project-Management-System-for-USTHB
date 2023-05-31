# Generated by Django 4.1.7 on 2023-05-20 21:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0004_alter_pub_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='skill',
            name='pourcentage',
            field=models.IntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(100), django.core.validators.MinValueValidator(10)]),
        ),
    ]
