import importlib
import sys
import types
import unittest
from unittest.mock import patch


class _Result:
    def __init__(self, data):
        self.data = data


class _ProductsTable:
    def __init__(self, product_row):
        self.product_row = dict(product_row)
        self.updated = None

    def select(self, *_args, **_kwargs):
        return self

    def update(self, data):
        self.updated = dict(data)
        return self

    def eq(self, *_args, **_kwargs):
        return self

    def execute(self):
        if self.updated is None:
            return _Result([dict(self.product_row)])
        self.product_row.update(self.updated)
        return _Result([dict(self.product_row)])


class _SupabaseStub:
    def __init__(self, product_row):
        self.products = _ProductsTable(product_row)

    def table(self, name):
        if name != "products":
            raise AssertionError(f"unexpected table {name}")
        return self.products


def load_resolve_job_module():
    sys.modules.pop("apps.worker.jobs.resolve_job", None)
    return importlib.import_module("apps.worker.jobs.resolve_job")


resolve_job = load_resolve_job_module()


class ResolveJobTests(unittest.TestCase):
    def test_resolve_job_replaces_placeholder_title_and_enqueues_generate(self):
        product_row = {
            "id": "prod-1",
            "tenant_id": "tenant-1",
            "gtin": "7891000100103",
            "title": "Produto Sem Título Gerado",
            "brand": "",
            "category": "",
            "description": "",
            "attributes": {},
            "images": [],
            "status": "pending",
        }
        supabase = _SupabaseStub(product_row)
        enqueued = []

        class IdentityResolverStub:
            def resolve_confidence(self, normalized, sources=None):
                self.normalized = normalized
                self.sources = sources
                return {"confidence": 0.87, "status": "resolved"}

            def should_proceed_to_listing(self, ident):
                return ident["status"] == "resolved"

        class FetchServiceStub:
            async def lookup_by_gtin(self, gtin):
                return types.SimpleNamespace(
                    gtin=gtin,
                    found=True,
                    source="openfoodfacts",
                    confidence=0.87,
                    data={
                        "title": "Café Torrado e Moído Tradicional 500g",
                        "brand": "Marca Teste",
                        "category": "cafe",
                        "description": "Café tradicional embalado a vácuo.",
                        "attributes": {"quantity": "500g"},
                        "images": ["https://example.com/cafe.jpg"],
                    },
                )

        class QueueStub:
            def __init__(self, connection=None):
                self.connection = connection

            def enqueue(self, job_name, args=(), kwargs=None):
                enqueued.append(
                    {
                        "job_name": job_name,
                        "args": args,
                        "kwargs": kwargs or {},
                    }
                )

        redis_stub = types.SimpleNamespace(
            Redis=types.SimpleNamespace(from_url=lambda _url: object())
        )
        rq_stub = types.SimpleNamespace(Queue=QueueStub)

        with patch.object(resolve_job, "get_normalizer") as get_normalizer, patch.object(
            resolve_job, "get_identity_resolver", return_value=IdentityResolverStub()
        ), patch.object(
            resolve_job, "get_product_fetch_service", return_value=FetchServiceStub()
        ), patch.dict(sys.modules, {"rq": rq_stub, "redis": redis_stub}):
            get_normalizer.return_value = types.SimpleNamespace(
                normalize_product=lambda product: dict(product)
            )

            result = resolve_job.product_resolve_handler(
                product_id="prod-1",
                tenant_id="tenant-1",
                supabase=supabase,
            )

        self.assertEqual(result["status"], "success")
        self.assertEqual(supabase.products.updated["title"], "Café Torrado e Moído Tradicional 500g")
        self.assertEqual(supabase.products.updated["brand"], "Marca Teste")
        self.assertEqual(
            supabase.products.updated["description"],
            "Café tradicional embalado a vácuo.",
        )
        self.assertEqual(
            supabase.products.updated["attributes"],
            {"quantity": "500g"},
        )
        self.assertEqual(
            enqueued[0]["job_name"],
            "apps.worker.jobs.generate_job.listing_generate_handler",
        )


if __name__ == "__main__":
    unittest.main()
