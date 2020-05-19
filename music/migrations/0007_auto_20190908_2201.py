# Generated by Django 2.2.5 on 2019-09-08 22:01

import django.db.models.deletion
from django.db import migrations, models

import music.models


class Migration(migrations.Migration):

    dependencies = [("music", "0006_auto_20160920_0724")]

    operations = [
        migrations.AlterField(
            model_name="activityestimate",
            name="content_type",
            field=models.ForeignKey(
                limit_choices_to=music.models.activity_content_type_choices,
                on_delete=django.db.models.deletion.PROTECT,
                to="contenttypes.ContentType",
            ),
        )
    ]
