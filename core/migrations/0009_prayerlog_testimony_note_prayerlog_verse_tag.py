from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_pushsubscription_reminderdelivery"),
    ]

    operations = [
        migrations.AddField(
            model_name="prayerlog",
            name="testimony_note",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="prayerlog",
            name="verse_tag",
            field=models.CharField(blank=True, max_length=200),
        ),
    ]
