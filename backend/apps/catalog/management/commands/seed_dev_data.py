"""Seed realistic development data (US1 demo / quickstart)."""

from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.catalog.models import Category, Product, UnitOfMeasure
from apps.movements.services import MovementService
from apps.warehouses.models import Location

User = get_user_model()


class Command(BaseCommand):
    help = "Seed reference data, demo users, items, and opening stock."

    def handle(self, *args, **options):
        admin_user, _ = User.objects.get_or_create(
            username="admin", defaults={"role": User.Role.ADMIN, "is_staff": True, "is_superuser": True}
        )
        admin_user.set_password("admin")
        admin_user.save(update_fields=["password"])
        manager_user, _ = User.objects.get_or_create(username="manager", defaults={"role": User.Role.MANAGER})
        manager_user.set_password("manager")
        manager_user.save(update_fields=["password"])
        staff_user, _ = User.objects.get_or_create(username="staff", defaults={"role": User.Role.STAFF})
        staff_user.set_password("staff")
        staff_user.save(update_fields=["password"])

        electronics, _ = Category.objects.get_or_create(
            name="Electronics", defaults={"description": "Consumer electronics"}
        )
        consumables, _ = Category.objects.get_or_create(name="Consumables")
        piece, _ = UnitOfMeasure.objects.get_or_create(name="Piece", symbol="pc")
        kilogram, _ = UnitOfMeasure.objects.get_or_create(name="Kilogram", symbol="kg", allow_fractional=True)
        main, _ = Location.objects.get_or_create(name="Main warehouse", code="MAIN")
        annex, _ = Location.objects.get_or_create(name="Annex", code="ANNEX")

        items = [
            (
                "HDD-2TB",
                "2TB Internal HDD",
                electronics,
                piece,
                Decimal("5"),
                Decimal("62.00"),
                Decimal("10"),
            ),
            ("MON-27", "27-inch Monitor", electronics, piece, Decimal("3"), Decimal("180.50"), Decimal("8")),
            (
                "SCREW-M3",
                "M3 Screws 100pk",
                consumables,
                piece,
                Decimal("50"),
                Decimal("3.25"),
                Decimal("20"),
            ),
            (
                "FLUX-500",
                "Solder Flux 500g",
                consumables,
                kilogram,
                Decimal("2.000"),
                Decimal("9.80"),
                Decimal("40.000"),
            ),
        ]
        service = MovementService()
        for sku, name, category, unit, reorder, cost, opening in items:
            product, created = Product.objects.get_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "category": category,
                    "unit": unit,
                    "reorder_level": reorder,
                    "unit_cost": cost,
                },
            )
            if created:
                service.record(
                    flow="receipt",
                    direction="in",
                    product=product,
                    location=main,
                    quantity=opening,
                    reason="Opening stock (seed)",
                    recorded_by=admin_user,
                )
                service.record(
                    flow="receipt",
                    direction="in",
                    product=product,
                    location=annex,
                    quantity=opening / 2,
                    reason="Opening stock (seed)",
                    recorded_by=admin_user,
                )
        self.stdout.write(
            self.style.SUCCESS("Seeded users, locations, categories, items, and opening stock.")
        )
