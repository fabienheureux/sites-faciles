# Generated by Django 5.1.1 on 2024-09-23 13:57

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sites_faciles_events", "0008_alter_evententrypage_body_alter_eventsindexpage_body"),
    ]

    operations = [
        migrations.AddField(
            model_name="evententrypage",
            name="source_url",
            field=models.URLField(
                blank=True, help_text="For imported pages, to allow updates.", null=True, verbose_name="Source URL"
            ),
        ),
        migrations.AddField(
            model_name="eventsindexpage",
            name="source_url",
            field=models.URLField(
                blank=True, help_text="For imported pages, to allow updates.", null=True, verbose_name="Source URL"
            ),
        ),
    ]
