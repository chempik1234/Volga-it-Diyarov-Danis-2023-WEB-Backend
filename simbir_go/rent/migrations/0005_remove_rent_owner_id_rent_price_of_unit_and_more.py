# Generated by Django 4.2.6 on 2023-10-22 09:26

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('rent', '0004_rename_finish_datetime_rent_time_end_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rent',
            name='owner_id',
        ),
        migrations.AddField(
            model_name='rent',
            name='price_of_unit',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='rent',
            name='renter_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]