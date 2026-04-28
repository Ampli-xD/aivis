from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
import asyncio
import os
from database import fetch_active_decks_db, batch_update_execution_time_db
from model_handler import handle_model_execution

# Pull interval from .env, default to 15 mins for production, 1 min for development/testing
CRON_INTERVAL_MIN = int(os.environ.get("CRON_INTERVAL_MIN", 15))

scheduler = AsyncIOScheduler()

async def execute_deck_task(deck):
    """
    Executes a deck by delegating each model's work to the model_handler.
    Runs models in parallel for performance.
    """
    print(f"Executing deck: {deck['id']} ({deck.get('name')})")
    
    # Run models in parallel
    tasks = [handle_model_execution(deck, model_id) for model_id in deck['model_ids']]
    await asyncio.gather(*tasks)
    
    print(f"Completed deck: {deck['id']}")

async def process_decks():
    # Capture base time at the very start for accuracy
    base_time = datetime.now()
    if base_time.tzinfo is None:
        base_time = base_time.astimezone()
        
    print(f"Cron job started at {base_time}")
    
    # 1. Fetch all active decks
    decks = fetch_active_decks_db()
    if not decks:
        print("No active decks found.")
        return

    current_time = base_time # Use the captured base_time for comparison too
    decks_to_run = []
    updates = []

    # 2. Filter decks that need to run
    for deck in decks:
        should_run = False
        next_exec_str = deck.get("next_execution_time")
        
        if next_exec_str is None:
            should_run = True
        else:
            try:
                if isinstance(next_exec_str, datetime):
                    next_exec = next_exec_str
                else:
                    next_exec = datetime.fromisoformat(next_exec_str.replace('Z', '+00:00'))
                
                if next_exec.tzinfo is not None and current_time.tzinfo is None:
                     current_time = current_time.astimezone()
                elif next_exec.tzinfo is None and current_time.tzinfo is not None:
                     next_exec = next_exec.replace(tzinfo=current_time.tzinfo)

                if next_exec <= current_time:
                    should_run = True
            except (ValueError, TypeError) as e:
                print(f"Error handling time for deck {deck['id']}: {e}")
                should_run = False

        if should_run:
            decks_to_run.append(deck)

    if not decks_to_run:
        print("No decks scheduled to run now.")
        return

    print(f"Executing {len(decks_to_run)} decks...")

    # 3. Execute tasks
    tasks = [execute_deck_task(deck) for deck in decks_to_run]
    await asyncio.gather(*tasks)

    # 4. Calculate new execution times
    for deck in decks_to_run:
        freq = deck.get("frequency", 1) 
        if not isinstance(freq, int):
            freq = 1
        
        # We add the CRON_INTERVAL_MIN * frequency to ensure they land in the next "slot"
        minutes_to_add = CRON_INTERVAL_MIN * freq
        next_time = base_time + timedelta(minutes=minutes_to_add)
        
        updates.append({
            "id": deck["id"],
            "user_id": deck["user_id"],
            "brand_id": deck["brand_id"],
            "name": deck["name"],
            "model_ids": deck["model_ids"],
            "region_ids": deck["region_ids"],
            "prompt_ids": deck["prompt_ids"],
            "frequency": deck["frequency"],
            "next_execution_time": next_time.isoformat()
        })

    # 5. Batch update
    if updates:
        print(f"Updating next_execution_time for {len(updates)} decks.")
        batch_update_execution_time_db(updates)

def start_scheduler():
    # Schedule the job to run as per environmental override
    scheduler.add_job(process_decks, 'interval', minutes=CRON_INTERVAL_MIN)
    scheduler.start()
