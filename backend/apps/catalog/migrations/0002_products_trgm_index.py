"""PostgreSQL-only pg_trgm index on Product.name (search latency, SC-005)."""

from django.db import migrations


def create_trgm_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    schema_editor.execute(
        "CREATE INDEX catalog_product_name_trgm ON catalog_product USING gin (name gin_trgm_ops)"
    )


def drop_trgm_index(apps, schema_editor):
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP INDEX IF EXISTS catalog_product_name_trgm")


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_trgm_index, drop_trgm_index),
    ]
