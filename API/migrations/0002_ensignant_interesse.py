# Generated by Django 4.1.7 on 2023-05-13 20:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('API', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ensignant',
            name='interesse',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]
