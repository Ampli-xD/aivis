import asyncio
from datetime import datetime
from database import create_instance_db, get_brand_db, get_model_db, get_region_db, get_prompt_db
from models import get_model


async def handle_model_execution(deck, model_id):
    """
    Handles execution of all prompts in a deck for a specific model.
    Fetches the AI response for each (prompt × region) combination and
    stores the result in the database. No metric processing is performed.
    """
    model_meta = get_model_db(str(model_id))
    if not model_meta:
        print(f"[model_handler] Model not found: {model_id}")
        return

    # Resolve model implementation from external_id (e.g. "gpt-4o-mini", "gpt-4.1")
    external_id = model_meta["external_id"]
    try:
        model = get_model(external_id)
    except ValueError as e:
        print(f"[model_handler] {e}")
        return

    # Shared metadata
    brand = get_brand_db(str(deck["brand_id"]))
    brand_name   = brand["name"]   if brand else "Unknown"
    brand_domain = brand["domain"] if brand else "unknown.com"

    initiated_at = datetime.now().astimezone()
    # Monthly bucket: first day of the month at 00:00:00
    time_bucket = initiated_at.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    async def process_instance(prompt_id, region_id):
        prompt_meta = get_prompt_db(str(prompt_id))
        if not prompt_meta:
            print(f"[model_handler] Prompt not found: {prompt_id}")
            return

        region_meta = get_region_db(str(region_id)) if region_id else None
        region_name = region_meta["name"] if region_meta else "Global"

        # Fetch response from the AI model
        response_data = await model.generate_response(
            prompt_meta["content"],
            region_meta=region_meta,
        )
        completed_at = datetime.now().astimezone()

        # Persist the instance — metrics left empty (processed separately later if needed)
        instance_data = {
            "time_bucket":    time_bucket,
            "initiated_at":   initiated_at,
            "completed_at":   completed_at,
            "user_id":        deck["user_id"],
            "brand_id":       deck["brand_id"],
            "deck_id":        deck["id"],
            "prompt_id":      prompt_id,
            "model_id":       model_id,
            "region_id":      region_id,
            "brand_name":     brand_name,
            "deck_name":      deck.get("name", "Unnamed Deck"),
            "model_name":     model_meta["model_name"],
            "prompt_content": prompt_meta["content"],
            "region_name":    region_name,
            "response_data":  response_data,
            "metrics":        {},  # No metric processing at this stage
        }

        create_instance_db(instance_data)
        print(f"[model_handler] Saved instance — prompt: {prompt_id} | region: {region_name} | model: {external_id}")

    # Fan out all (prompt × region) combos in parallel
    region_ids = deck.get("region_ids") or [None]
    tasks = [
        process_instance(prompt_id, region_id)
        for prompt_id in deck["prompt_ids"]
        for region_id in region_ids
    ]

    if tasks:
        await asyncio.gather(*tasks)

    print(f"[model_handler] Completed deck: {deck['id']} | model: {external_id}")
