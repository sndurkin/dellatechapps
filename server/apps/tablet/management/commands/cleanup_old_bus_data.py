"""
Management command to delete old BusData records.

This command deletes BusData records that are 10 days old or older
based on their created_at timestamp.

Usage:
    python manage.py cleanup_old_bus_data
    python manage.py cleanup_old_bus_data --days 10
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from server.apps.tablet.models import BusData


class Command(BaseCommand):
    help = 'Delete BusData records older than specified days (default: 10 days)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=10,
            help='Number of days old records should be before deletion (default: 10)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']

        cutoff_date = timezone.now() - timedelta(days=days)
        old_records = BusData.objects.filter(created_at__lt=cutoff_date)
        count = old_records.count()

        if count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'No BusData records found older than {days} days.'
                )
            )
            return

        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {count} BusData record(s) older than {days} days '
                    f'(created before {cutoff_date.strftime("%Y-%m-%d %H:%M:%S")})'
                )
            )
            # Show a sample of what would be deleted
            sample = old_records[:5]
            for record in sample:
                self.stdout.write(
                    f'  - {record} (created: {record.created_at})'
                )
            if count > 5:
                self.stdout.write(f'  ... and {count - 5} more')
        else:
            # Delete the records
            deleted_count, _ = old_records.delete()
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} BusData record(s) older than {days} days.'
                )
            )
