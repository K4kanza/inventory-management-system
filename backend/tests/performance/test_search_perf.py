"""Performance and search sanity tests (SC-005 area).

The functional search test runs on any backend; the timing/plan checks require
PostgreSQL (test marker ``postgres``) and are deselected unless requested.
"""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext

from apps.catalog.models import Product


@pytest.mark.django_db
def test_search_is_database_side(db, category, unit):
    for i in range(30):
        Product.objects.create(
            sku=f"SKU-{i:03d}",
            name=f"Widget {i:03d}" if i % 3 else "Gadget special",
            category=category,
            unit=unit,
            reorder_level=0,
        )
    with CaptureQueriesContext(connection) as context:
        results = list(Product.objects.filter(name__icontains="gadget"))
    assert len(results) == 10
    assert len(context.captured_queries) == 1


@pytest.mark.postgres
@pytest.mark.slow
@pytest.mark.django_db(transaction=True)
def test_search_latency_with_trgm(db, category, unit):
    import time

    Product.objects.bulk_create(
        Product(
            sku=f"BULK-{i:06d}",
            name=f"Bulk part {i:06d}",
            category=category,
            unit=unit,
            reorder_level=0,
        )
        for i in range(5000)
    )
    start = time.perf_counter()
    count = Product.objects.filter(name__icontains="bulk part 0049").count()
    elapsed = time.perf_counter() - start
    assert count == 1
    assert elapsed < 2.0, f"search took {elapsed:.3f}s"
