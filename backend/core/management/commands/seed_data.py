"""
seed_data management command — Creates demo tenant, user, and ingests all sample files.

Usage: python manage.py seed_data

Creates:
- Tenant: "Acme Corp"
- User: analyst@acme.com / password123
- Runs all three sample files through the ingestion pipeline
"""
import os
from pathlib import Path
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile

from users.models import Tenant, User
from ingestion.models import DataSource, IngestionRun
from ingestion.parsers.sap_parser import parse_sap_file
from ingestion.parsers.utility_parser import parse_utility_file
from ingestion.parsers.travel_parser import parse_travel_file


class Command(BaseCommand):
    help = 'Seed database with demo tenant, user, and sample data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🌱 Starting database seed...'))

        # Determine sample_data directory
        # The sample_data folder is at the repo root (two levels up from manage.py)
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent
        repo_root = backend_dir.parent
        sample_dir = repo_root / 'sample_data'

        if not sample_dir.exists():
            self.stdout.write(self.style.ERROR(
                f'❌ sample_data directory not found at {sample_dir}'
            ))
            return

        # 1. Create Tenant
        tenant, created = Tenant.objects.get_or_create(
            name='Acme Corp',
            defaults={'slug': 'acme-corp'},
        )
        status_msg = 'Created' if created else 'Already exists'
        self.stdout.write(f'  ✅ Tenant "Acme Corp" — {status_msg}')

        # 2. Create User
        user, created = User.objects.get_or_create(
            username='analyst@acme.com',
            defaults={
                'email': 'analyst@acme.com',
                'first_name': 'Analyst',
                'last_name': 'User',
                'tenant': tenant,
                'is_active': True,
            },
        )
        if created:
            user.set_password('password123')
            user.save()
            self.stdout.write('  ✅ User "analyst@acme.com" — Created')
        else:
            # Ensure tenant is set even if user existed
            if not user.tenant:
                user.tenant = tenant
                user.save()
            self.stdout.write('  ✅ User "analyst@acme.com" — Already exists')

        # 3. Ingest sample files
        sample_files = [
            ('SAP', 'sap_export.csv', 'SAP Fuel Export', parse_sap_file),
            ('UTILITY', 'utility_export.csv', 'Utility Electricity', parse_utility_file),
            ('TRAVEL', 'travel_export.csv', 'Corporate Travel', parse_travel_file),
        ]

        for source_type, filename, source_name, parser_func in sample_files:
            filepath = sample_dir / filename

            if not filepath.exists():
                self.stdout.write(self.style.WARNING(
                    f'  ⚠️  {filename} not found, skipping...'
                ))
                continue

            self.stdout.write(f'  📄 Ingesting {filename}...')

            # Create or get DataSource
            data_source, _ = DataSource.objects.get_or_create(
                tenant=tenant,
                source_type=source_type,
                defaults={'name': source_name},
            )

            # Create IngestionRun
            run = IngestionRun.objects.create(
                data_source=data_source,
                status='PROCESSING',
                triggered_by=user,
            )

            # Read file and parse
            try:
                with open(filepath, 'rb') as f:
                    row_count, error_count = parser_func(f, run, tenant, user)

                from django.utils import timezone
                run.status = 'COMPLETE'
                run.row_count = row_count
                run.error_count = error_count
                run.completed_at = timezone.now()
                run.save()

                self.stdout.write(self.style.SUCCESS(
                    f'     ✅ {source_type}: {row_count} rows parsed, '
                    f'{error_count} errors'
                ))
            except Exception as e:
                from django.utils import timezone
                run.status = 'FAILED'
                run.error_log = str(e)
                run.completed_at = timezone.now()
                run.save()
                self.stdout.write(self.style.ERROR(
                    f'     ❌ {source_type} failed: {e}'
                ))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(
            '🎉 Seed complete! Login with: analyst@acme.com / password123'
        ))
