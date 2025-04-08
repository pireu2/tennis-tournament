# Generated by Django 5.2 on 2025-04-08 09:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="referee",
            name="certification_level",
            field=models.CharField(
                choices=[
                    ("BRONZE", "Bronze Level"),
                    ("SILVER", "Silver Level"),
                    ("GOLD", "Gold Level"),
                    ("PLATINUM", "Platinum Level"),
                ],
                default="BRONZE",
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name="tennisplayer",
            name="date_of_birth",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="tennisplayer",
            name="gender",
            field=models.CharField(
                choices=[("M", "Male"), ("F", "Female"), ("O", "Other")],
                default="O",
                max_length=1,
            ),
        ),
    ]
