# Generated by Django 1.9.6 on 2016-05-26 04:47
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("artist", "0006_updatetitles"),
    ]

    operations = [
        migrations.CreateModel(
            name="ArtistAdmin",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("musician", "Musician"),
                            ("manager", "Manager"),
                            ("producer", "Producer"),
                        ],
                        help_text="The relationship of this user to the artist",
                        max_length=12,
                    ),
                ),
                (
                    "artist",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="artist.Artist"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        )
    ]
