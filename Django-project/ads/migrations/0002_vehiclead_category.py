# Generated by Django 4.1.2 on 2022-11-10 16:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vehiclead',
            name='category',
            field=models.CharField(blank=True, default=None, max_length=1024, null=True),
        ),
    ]
