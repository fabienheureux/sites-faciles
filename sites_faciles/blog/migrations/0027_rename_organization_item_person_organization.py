# Generated by Django 5.0.6 on 2024-07-08 16:16

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("sites_faciles_blog", "0026_alter_organization_options"),
    ]

    operations = [
        migrations.RenameField(
            model_name="person",
            old_name="organization_item",
            new_name="organization",
        ),
    ]
