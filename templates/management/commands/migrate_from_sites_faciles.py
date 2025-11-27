"""
Django management command to rename tables and update migration history.

This command:
1. Renames database tables by prefixing them with 'wagtail_dsfr_'
2. Updates django_migrations table to reflect the new app names

Usage:
    python manage.py rename_to_wagtail_dsfr
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Rename tables and migrations to use wagtail_dsfr_ prefix"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Preview changes without executing them",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip confirmation prompt",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        no_input = options["no_input"]

        self.stdout.write(self.style.SUCCESS("Starting database rename operations..."))
        self.stdout.write("=" * 60)

        with connection.cursor() as cursor:
            # Step 1: Get list of tables to rename
            self.stdout.write("\n1. Finding tables to rename...")
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                  AND (
                    table_name LIKE 'content_manager_%'
                    OR table_name LIKE 'blog_%'
                    OR table_name LIKE 'events_%'
                    OR table_name LIKE 'forms_%'
                  )
                ORDER BY table_name;
            """)

            tables_to_rename = cursor.fetchall()

            if not tables_to_rename:
                self.stdout.write(self.style.WARNING("No tables found to rename."))
                return

            self.stdout.write(self.style.SUCCESS(f"Found {len(tables_to_rename)} tables to rename:"))
            table_renames = []
            for (table_name,) in tables_to_rename:
                if table_name.startswith("content_manager_"):
                    new_name = table_name.replace("content_manager_", "wagtail_dsfr_content_manager_")
                else:
                    new_name = "wagtail_dsfr_" + table_name
                table_renames.append((table_name, new_name))
                self.stdout.write(f"  - {table_name} → {new_name}")

            # Step 2: Preview migration updates
            self.stdout.write("\n2. Previewing migration updates...")
            cursor.execute("""
                SELECT
                    app,
                    COUNT(*) as migration_count
                FROM django_migrations
                WHERE app IN ('blog', 'forms', 'content_manager', 'events')
                GROUP BY app
                ORDER BY app;
            """)

            migrations_to_update = cursor.fetchall()

            if not migrations_to_update:
                self.stdout.write(self.style.WARNING("No migrations found to update."))
                migration_updates = []
            else:
                self.stdout.write(self.style.SUCCESS(f"Found migrations in {len(migrations_to_update)} apps:"))
                migration_updates = []
                for app, count in migrations_to_update:
                    new_app = "wagtail_dsfr_" + app
                    migration_updates.append((app, new_app, count))
                    self.stdout.write(f"  - {app}: {count} migration(s) → {new_app}")

            if dry_run:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(self.style.SUCCESS("DRY RUN: No changes were made."))
                return

            # Step 3: Confirm before proceeding
            if not no_input:
                self.stdout.write("\n" + "=" * 60)
                confirm = input("Proceed with renaming? (yes/no): ")
                if confirm.lower() != "yes":
                    self.stdout.write(self.style.WARNING("Operation cancelled."))
                    return

            self.stdout.write("\n3. Starting transaction...")

            # Step 4: Rename tables
            self.stdout.write("\n4. Renaming tables...")
            renamed_count = 0
            for table_name, new_name in table_renames:
                try:
                    cursor.execute(f'ALTER TABLE "{table_name}" RENAME TO "{new_name}";')
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Renamed: {table_name} → {new_name}"))
                    renamed_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"  ✗ Error renaming {table_name}: {e}"))

            self.stdout.write(self.style.SUCCESS(f"\nRenamed {renamed_count} tables."))

            # Step 5: Update django_migrations
            if migration_updates:
                self.stdout.write("\n5. Updating django_migrations table...")
                cursor.execute("""
                    UPDATE django_migrations
                    SET app = 'wagtail_dsfr_' || app
                    WHERE app IN ('blog', 'forms', 'content_manager', 'events');
                """)
                updated_rows = cursor.rowcount
                self.stdout.write(self.style.SUCCESS(f"  ✓ Updated {updated_rows} migration records"))

                # Step 6: Verify changes
                self.stdout.write("\n6. Verifying changes...")
                cursor.execute("""
                    SELECT app, COUNT(*) as count
                    FROM django_migrations
                    WHERE app LIKE 'wagtail_dsfr_%'
                    GROUP BY app
                    ORDER BY app;
                """)

                results = cursor.fetchall()
                self.stdout.write("Migration records after update:")
                for app, count in results:
                    self.stdout.write(f"  - {app}: {count} migration(s)")

            self.stdout.write("\n" + "=" * 60)
            self.stdout.write(self.style.SUCCESS("✓ All operations completed successfully!"))
            self.stdout.write("\n" + self.style.WARNING("IMPORTANT NEXT STEPS:"))
            self.stdout.write("1. Update your Django model Meta.db_table attributes")
            self.stdout.write("2. Verify INSTALLED_APPS in settings.py matches new app names")
            self.stdout.write("3. Test your application thoroughly")
