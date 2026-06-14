"""Create test data for development."""

from django.core.management.base import BaseCommand
from django.conf import settings

from apps.users.models import CustomUser
from apps.tenants.models import Tenant, UserTenantRole


class Command(BaseCommand):
    help = "Create test data: admin user, tenants, members, API tokens"

    def handle(self, *args, **options):
        self._create_admin()
        self._create_tenants()
        self.stdout.write(self.style.SUCCESS("Test data created successfully"))

    def _create_admin(self):
        if not CustomUser.objects.filter(email="admin@example.com").exists():
            CustomUser.objects.create_superuser(
                email="admin@example.com",
                password="admin123",
            )
            self.stdout.write("  Created admin user: admin@example.com")
        else:
            self.stdout.write("  Admin user already exists")

    def _create_tenants(self):
        admin = CustomUser.objects.get(email="admin@example.com")

        if not Tenant.objects.filter(slug="acme-corp").exists():
            acme = Tenant.objects.create(
                name="Acme Corp",
                slug="acme-corp",
                description="Main development tenant",
                rate_limit=1000,
                max_users=50,
                is_active=True,
            )
            UserTenantRole.objects.create(
                user=admin,
                tenant=acme,
                role=UserTenantRole.OWNER,
            )
            self.stdout.write("  Created tenant: Acme Corp (owner: admin)")

        if not Tenant.objects.filter(slug="demo-inc").exists():
            demo = Tenant.objects.create(
                name="Demo Inc",
                slug="demo-inc",
                description="Demo tenant for testing",
                rate_limit=500,
                max_users=20,
                is_active=True,
            )
            UserTenantRole.objects.create(
                user=admin,
                tenant=demo,
                role=UserTenantRole.OWNER,
            )
            self.stdout.write("  Created tenant: Demo Inc (owner: admin)")

        if not CustomUser.objects.filter(email="member@example.com").exists():
            member = CustomUser.objects.create_user(
                email="member@example.com",
                password="member123",
            )
            member.is_email_verified = True
            member.save()
            acme = Tenant.objects.get(slug="acme-corp")
            UserTenantRole.objects.create(
                user=member,
                tenant=acme,
                role=UserTenantRole.MEMBER,
            )
            self.stdout.write("  Created member: member@example.com (Acme Corp)")

        if not CustomUser.objects.filter(email="admin2@example.com").exists():
            admin2 = CustomUser.objects.create_user(
                email="admin2@example.com",
                password="admin2123",
            )
            admin2.is_email_verified = True
            admin2.save()
            acme = Tenant.objects.get(slug="acme-corp")
            UserTenantRole.objects.create(
                user=admin2,
                tenant=acme,
                role=UserTenantRole.ADMIN,
            )
            self.stdout.write("  Created admin2: admin2@example.com (Acme Corp)")
