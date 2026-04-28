from fastapi import APIRouter, Header, HTTPException, Depends
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from dotenv import load_dotenv
import os

load_dotenv()

from database import (
    # Models
    get_all_models_db, create_model_db, update_model_db, delete_model_db,
    # Regions
    get_all_regions_db, create_region_db, update_region_db, delete_region_db,
    # Users
    get_all_users_db, get_user_db, update_user_db, delete_user_db,
    # Brands
    get_all_brands_db, get_brand_db, update_brand_db, delete_brand_db,
    # Decks
    get_all_decks_db, get_deck_db, update_deck_db, delete_deck_db, fetch_active_decks_db,
    # Prompts
    get_all_prompts_db, get_brand_prompts_db, get_prompt_db, update_prompt_db, delete_prompt_db,
    # Instances
    get_instances_db, get_instance_db,
)

ADMIN_KEY = os.environ.get("ADMIN_KEY", "aivis-admin-dev")

router = APIRouter(prefix="/admin", tags=["admin"])

# --- Auth Guard ---
def verify_admin(x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")

# --- Schemas ---
class AdminModelCreate(BaseModel):
    provider: str
    model_name: str
    external_id: str
    pricing: Optional[Dict[str, float]] = {}

class AdminModelUpdate(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    external_id: Optional[str] = None
    pricing: Optional[Dict[str, float]] = None

class AdminRegionCreate(BaseModel):
    name: str
    country_code: str
    region: Optional[str] = None
    city: Optional[str] = None

class AdminRegionUpdate(BaseModel):
    name: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

class AdminUserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    slack_user_id: Optional[str] = None

class AdminBrandUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

class AdminDeckUpdate(BaseModel):
    name: Optional[str] = None
    to_execute: Optional[bool] = None
    frequency: Optional[int] = None

class AdminPromptUpdate(BaseModel):
    content: Optional[str] = None
    notes: Optional[str] = None

# ============================
# VERIFY KEY
# ============================
@router.post("/verify")
async def admin_verify_key(x_admin_key: str = Header(...)):
    if x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Invalid admin key")
    return {"verified": True}

# ============================
# OVERVIEW
# ============================
@router.get("/overview", dependencies=[Depends(verify_admin)])
async def admin_overview():
    models  = get_all_models_db()
    regions = get_all_regions_db()
    users   = get_all_users_db()
    brands  = get_all_brands_db()
    decks   = get_all_decks_db()
    prompts = get_all_prompts_db()
    instances = get_instances_db()

    for u in users:
        u.pop("password_hash", None)

    return {
        "counts": {
            "models": len(models),
            "regions": len(regions),
            "users": len(users),
            "brands": len(brands),
            "decks": len(decks),
            "active_decks": sum(1 for d in decks if d.get("to_execute")),
            "prompts": len(prompts),
            "instances": len(instances),
        },
        "models":  models,
        "regions": regions,
        "users":   users,
        "brands":  brands,
        "decks":   decks,
        "prompts": prompts,
    }

# ============================
# MODELS
# ============================
@router.get("/models", dependencies=[Depends(verify_admin)])
async def admin_list_models():
    return get_all_models_db()

@router.post("/models", status_code=201, dependencies=[Depends(verify_admin)])
async def admin_create_model(body: AdminModelCreate):
    m = create_model_db(body.provider, body.model_name, body.external_id, body.pricing or {})
    if not m: raise HTTPException(status_code=500, detail="Failed to create model")
    return m

@router.patch("/models/{model_id}", dependencies=[Depends(verify_admin)])
async def admin_update_model(model_id: str, body: AdminModelUpdate):
    m = update_model_db(model_id, body.dict(exclude_unset=True))
    if not m: raise HTTPException(status_code=404, detail="Model not found")
    return m

@router.delete("/models/{model_id}", dependencies=[Depends(verify_admin)])
async def admin_delete_model(model_id: str):
    if not delete_model_db(model_id): raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted", "id": model_id}

# ============================
# REGIONS
# ============================
@router.get("/regions", dependencies=[Depends(verify_admin)])
async def admin_list_regions():
    return get_all_regions_db()

@router.post("/regions", status_code=201, dependencies=[Depends(verify_admin)])
async def admin_create_region(body: AdminRegionCreate):
    r = create_region_db(body.name, body.country_code, body.region, body.city)
    if not r: raise HTTPException(status_code=500, detail="Failed to create region")
    return r

@router.patch("/regions/{region_id}", dependencies=[Depends(verify_admin)])
async def admin_update_region(region_id: str, body: AdminRegionUpdate):
    r = update_region_db(region_id, body.dict(exclude_unset=True))
    if not r: raise HTTPException(status_code=404, detail="Region not found")
    return r

@router.delete("/regions/{region_id}", dependencies=[Depends(verify_admin)])
async def admin_delete_region(region_id: str):
    if not delete_region_db(region_id): raise HTTPException(status_code=404, detail="Region not found")
    return {"message": "Region deleted", "id": region_id}

# ============================
# USERS
# ============================
@router.get("/users", dependencies=[Depends(verify_admin)])
async def admin_list_users():
    users = get_all_users_db()
    for u in users: u.pop("password_hash", None)
    return users

@router.get("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def admin_get_user(user_id: str):
    u = get_user_db(user_id)
    if not u: raise HTTPException(status_code=404, detail="User not found")
    u.pop("password_hash", None)
    return u

@router.patch("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def admin_update_user(user_id: str, body: AdminUserUpdate):
    u = update_user_db(user_id, body.dict(exclude_unset=True))
    if not u: raise HTTPException(status_code=404, detail="User not found")
    u.pop("password_hash", None)
    return u

@router.delete("/users/{user_id}", dependencies=[Depends(verify_admin)])
async def admin_delete_user(user_id: str):
    if not delete_user_db(user_id): raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted", "id": user_id}

# ============================
# BRANDS
# ============================
@router.get("/brands", dependencies=[Depends(verify_admin)])
async def admin_list_brands():
    return get_all_brands_db()

@router.get("/brands/{brand_id}", dependencies=[Depends(verify_admin)])
async def admin_get_brand(brand_id: str):
    b = get_brand_db(brand_id)
    if not b: raise HTTPException(status_code=404, detail="Brand not found")
    return b

@router.patch("/brands/{brand_id}", dependencies=[Depends(verify_admin)])
async def admin_update_brand(brand_id: str, body: AdminBrandUpdate):
    b = update_brand_db(brand_id, body.dict(exclude_unset=True))
    if not b: raise HTTPException(status_code=404, detail="Brand not found")
    return b

@router.delete("/brands/{brand_id}", dependencies=[Depends(verify_admin)])
async def admin_delete_brand(brand_id: str):
    if not delete_brand_db(brand_id): raise HTTPException(status_code=404, detail="Brand not found")
    return {"message": "Brand deleted", "id": brand_id}

# ============================
# DECKS
# ============================
@router.get("/decks", dependencies=[Depends(verify_admin)])
async def admin_list_decks():
    return get_all_decks_db()

@router.get("/decks/{deck_id}", dependencies=[Depends(verify_admin)])
async def admin_get_deck(deck_id: str):
    d = get_deck_db(deck_id)
    if not d: raise HTTPException(status_code=404, detail="Deck not found")
    return d

@router.patch("/decks/{deck_id}", dependencies=[Depends(verify_admin)])
async def admin_update_deck(deck_id: str, body: AdminDeckUpdate):
    d = update_deck_db(deck_id, body.dict(exclude_unset=True))
    if not d: raise HTTPException(status_code=404, detail="Deck not found")
    return d

@router.delete("/decks/{deck_id}", dependencies=[Depends(verify_admin)])
async def admin_delete_deck(deck_id: str):
    if not delete_deck_db(deck_id): raise HTTPException(status_code=404, detail="Deck not found")
    return {"message": "Deck deleted", "id": deck_id}

# ============================
# PROMPTS
# ============================
@router.get("/prompts", dependencies=[Depends(verify_admin)])
async def admin_list_prompts(brand_id: Optional[str] = None):
    return get_brand_prompts_db(brand_id) if brand_id else get_all_prompts_db()

@router.get("/prompts/{prompt_id}", dependencies=[Depends(verify_admin)])
async def admin_get_prompt(prompt_id: str):
    p = get_prompt_db(prompt_id)
    if not p: raise HTTPException(status_code=404, detail="Prompt not found")
    return p

@router.patch("/prompts/{prompt_id}", dependencies=[Depends(verify_admin)])
async def admin_update_prompt(prompt_id: str, body: AdminPromptUpdate):
    p = update_prompt_db(prompt_id, body.dict(exclude_unset=True))
    if not p: raise HTTPException(status_code=404, detail="Prompt not found")
    return p

@router.delete("/prompts/{prompt_id}", dependencies=[Depends(verify_admin)])
async def admin_delete_prompt(prompt_id: str):
    if not delete_prompt_db(prompt_id): raise HTTPException(status_code=404, detail="Prompt not found")
    return {"message": "Prompt deleted", "id": prompt_id}

# ============================
# INSTANCES
# ============================
@router.get("/instances", dependencies=[Depends(verify_admin)])
async def admin_list_instances(
    deck_id: Optional[str] = None,
    model_id: Optional[str] = None,
    prompt_id: Optional[str] = None,
    region_id: Optional[str] = None,
):
    return get_instances_db(deck_id=deck_id, model_id=model_id, prompt_id=prompt_id, region_id=region_id)

@router.get("/instances/{instance_id}", dependencies=[Depends(verify_admin)])
async def admin_get_instance(instance_id: str):
    i = get_instance_db(instance_id)
    if not i: raise HTTPException(status_code=404, detail="Instance not found")
    return i

