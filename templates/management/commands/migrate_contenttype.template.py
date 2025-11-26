"""
Django management command to migrate ContentType app labels from Sites Faciles to {package_name}.

This command updates ContentType records in the database when migrating from a Sites Faciles
website to the packaged version of {package_name}.

Usage:
    python manage.py migrate_contenttype [--dry-run]
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from wagtail.models import Page


class Command(BaseCommand):
    help = "Migrate ContentType app labels from Sites Faciles to {package_name}"

    # Mapping of old app labels to new app labels
    APP_LABEL_MAPPING = {
        "blog": "{package_name}_blog",
        "events": "{package_name}_events",
        "forms": "{package_name}_forms",
        "content_manager": "{package_name}_content_manager",
        "config": "{package_name}_config",
    }

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))

        # Get all old and new ContentTypes
        old_app_labels = list(self.APP_LABEL_MAPPING.keys())
        new_app_labels = list(self.APP_LABEL_MAPPING.values())

        old_cts = ContentType.objects.filter(app_label__in=old_app_labels)
        new_cts = ContentType.objects.filter(app_label__in=new_app_labels)

        if not old_cts.exists():
            self.stdout.write(
                self.style.SUCCESS(
                    "✓ No old ContentTypes found. Migration already complete or not needed."
                )
            )
            return

        # Build mapping dictionaries
        old_cts_dict = {}
        for ct in old_cts:
            key = (ct.app_label, ct.model)
            old_cts_dict[key] = ct

        new_cts_dict = {}
        for ct in new_cts:
            # Map back to original app label for comparison
            original_app_label = None
            for old_label, new_label in self.APP_LABEL_MAPPING.items():
                if ct.app_label == new_label:
                    original_app_label = old_label
                    break
            if original_app_label:
                key = (original_app_label, ct.model)
                new_cts_dict[key] = ct

        self.stdout.write(f"\nFound {old_cts.count()} old ContentType(s) to migrate:")
        for ct in old_cts:
            self.stdout.write(f"  - {ct.app_label}.{ct.model} (id={ct.id})")

        # Check for missing new ContentTypes
        missing_mappings = []
        for (old_app, model), old_ct in old_cts_dict.items():
            if (old_app, model) not in new_cts_dict:
                missing_mappings.append(f"{old_app}.{model}")

        if missing_mappings:
            self.stdout.write(
                self.style.ERROR(
                    f"\n✗ Missing new ContentTypes for: {', '.join(missing_mappings)}"
                )
            )
            self.stdout.write(
                self.style.WARNING(
                    "\nPlease ensure all {package_name} apps are in INSTALLED_APPS "
                    "and run 'python manage.py migrate' first."
                )
            )
            raise CommandError("Cannot proceed - missing new ContentTypes")

        # Show what will be updated
        self.stdout.write(f"\nWill update {Page.objects.filter(content_type__in=old_cts).count()} page(s)")

        if not dry_run:
            self.stdout.write("\nProceeding with migration...")

            try:
                with transaction.atomic():
                    # Update Page.content_type references
                    updated_count = 0
                    for (old_app, model), old_ct in old_cts_dict.items():
                        new_ct = new_cts_dict.get((old_app, model))
                        if new_ct:
                            count = Page.objects.filter(content_type=old_ct).update(
                                content_type=new_ct
                            )
                            if count > 0:
                                self.stdout.write(
                                    f"  Updated {count} page(s): {old_ct.app_label}.{old_ct.model} → "
                                    f"{new_ct.app_label}.{new_ct.model}"
                                )
                                updated_count += count

                    # Delete old ContentTypes
                    deleted_count, _ = old_cts.delete()

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\n✓ Successfully migrated {updated_count} page(s) and "
                            f"removed {deleted_count} old ContentType(s)"
                        )
                    )

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"\n✗ Migration failed: {e}"))
                raise CommandError(f"Migration failed: {e}")
        else:
            self.stdout.write(
                self.style.WARNING("\nDry run complete. Run without --dry-run to apply changes.")
            )
