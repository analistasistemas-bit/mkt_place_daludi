import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

from apps.api.deps import get_supabase_admin_client
from apps.api.services.pipeline import get_pipeline

async def run():
    print("Testing pipeline directly with GTIN 7891020399778...")
    supabase = get_supabase_admin_client()
    res = supabase.table("products").select("*").eq("id", "6f6b3a6f-7e4a-444b-8bcc-d36ddd5fcc1d").execute()
    if not res.data:
        print("Produto não encontrado.")
        return
        
    product_data = res.data[0]
    tenant_id = product_data["tenant_id"]
    
    pipeline = get_pipeline()
    result = await pipeline.execute(
        product_data=product_data,
        tenant_id=tenant_id,
        sources=[{"source_type": "stub"}],
        tenant_settings={"default_margin": 0.3}
    )
    
    print(f"Success: {result.success}")
    if not result.success:
        print(f"Error at stage {result.stage}: {result.error}")
    else:
        print(f"Listing generated with status: {result.listing.get('status')}")

if __name__ == "__main__":
    asyncio.run(run())
