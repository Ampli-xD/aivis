from fastapi import FastAPI, Body, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import json
import asyncio
from openai import AsyncOpenAI

from cron import start_scheduler, scheduler, CRON_INTERVAL_MIN
from admin_router import router as admin_router
from database import (
    create_deck_db, get_deck_db, update_deck_db, delete_deck_db, reset_execution_times_db, get_brand_decks_db,
    create_user_db, get_user_db, get_all_users_db, update_user_db, delete_user_db, get_user_by_email,
    create_brand_db, get_user_brands_db, update_brand_db, delete_brand_db, get_dashboard_summary_db,
    create_model_db, get_all_models_db, update_model_db, delete_model_db,
    create_region_db, get_all_regions_db, update_region_db, delete_region_db,
    create_prompt_db, get_all_prompts_db, get_brand_prompts_db, get_prompt_db, update_prompt_db, delete_prompt_db,
    get_instances_db, get_instance_db,
    # Analytics
    get_unprocessed_instances_db, update_instance_metrics_db
)

# --- Auth Config ---
import os
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable is not set. Refusing to start.")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 1 day

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("id")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception

app = FastAPI(title="AiVis Backend", version="1.0.0")
app.include_router(admin_router)

# --- CORS config ---
cors_env = os.environ.get("CORS_ORIGINS", "")
cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()] if cors_env else []
# Always allow local dev origins
cors_origins += [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:80",
    "http://127.0.0.1:80",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "cron_interval": CRON_INTERVAL_MIN
    }

# --- Pydantic Models ---

class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    slack_user_id: Optional[str] = None

class PasswordUpdate(BaseModel):
    current_password: str
    new_password: str

class BrandBase(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

class BrandCreate(BrandBase):
    user_id: Optional[UUID] = None # Make optional for the schema, filled from token

class BrandUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

class ModelBase(BaseModel):
    provider: str
    model_name: str
    external_id: str
    pricing: Optional[Dict[str, float]] = Field(
        default_factory=dict,
        description="Cost per 1M tokens: {input, cached_input, output}"
    )

class ModelCreate(ModelBase):
    pass

class ModelUpdate(BaseModel):
    provider: Optional[str] = None
    model_name: Optional[str] = None
    external_id: Optional[str] = None
    pricing: Optional[Dict[str, float]] = None

class RegionBase(BaseModel):
    name: str
    country_code: str
    region: Optional[str] = None
    city: Optional[str] = None

class RegionCreate(RegionBase):
    pass

class RegionUpdate(BaseModel):
    name: Optional[str] = None
    country_code: Optional[str] = None
    region: Optional[str] = None
    city: Optional[str] = None

class PromptBase(BaseModel):
    content: str
    notes: Optional[str] = None

class PromptCreate(PromptBase):
    brand_id: Optional[UUID] = None

class PromptUpdate(BaseModel):
    content: Optional[str] = None
    notes: Optional[str] = None

class DeckBase(BaseModel):
    user_id: Optional[UUID] = None
    brand_id: UUID
    name: str
    model_ids: List[UUID]
    region_ids: Optional[List[UUID]] = []
    prompt_ids: List[UUID]
    frequency: int
    to_execute: bool = True

class DeckCreate(DeckBase):
    pass

class DeckUpdate(BaseModel):
    user_id: Optional[UUID] = None
    brand_id: Optional[UUID] = None
    name: Optional[str] = None
    model_ids: Optional[List[UUID]] = None
    region_ids: Optional[List[UUID]] = None
    prompt_ids: Optional[List[UUID]] = None
    frequency: Optional[int] = None
    to_execute: Optional[bool] = None

# --- Lifecycle ---

@app.on_event("startup")
async def startup_event():
    start_scheduler()
    print("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("Scheduler shutdown")
    reset_execution_times_db()
    print("Execution times reset")

# --- Endpoints ---

@app.get("/")
async def root():
    return {"message": "AiVis Backend API"}

from fastapi.responses import JSONResponse

@app.exception_handler(422)
async def validation_exception_handler(request, exc):
    print(f"ERROR: 422 Validation Failed on {request.url.path}")
    print(f"Errors: {exc.errors()}")
    # Attempt to read body for debugging (be careful, might consume it)
    try:
        body = await request.json()
        print(f"Request JSON: {body}")
    except:
        print("Could not parse request body as JSON")
        
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors(), "body_received": "check_server_logs"},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    import traceback
    print(f"CRITICAL ERROR: {str(exc)}")
    traceback.print_exc()
    response = JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
    )
    # Add CORS headers manually to error responses to help frontend debugging
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.get("/health")
async def health_check():
    return {"status": "ok"}

# --- Users ---

@app.post("/users", status_code=201)
async def create_user(user: UserCreate):
    # Check if user already exists
    if get_user_by_email(user.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
    new_user = create_user_db(user.email, hashed_password, user.full_name)
    if not new_user:
        raise HTTPException(status_code=500, detail="Failed to create user")
    
    new_user.pop("password_hash", None)
    return new_user

@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = get_user_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["email"], "id": str(user["id"])}, 
        expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users")
async def list_users():
    users = get_all_users_db()
    for u in users:
        u.pop("password_hash", None)
    return users

@app.get("/users/{user_id}")
async def get_user(user_id: UUID):
    user = get_user_db(str(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("password_hash", None)
    return user

@app.patch("/users/me/password")
async def change_password(body: PasswordUpdate, user_id: str = Depends(get_current_user)):
    user = get_user_db(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not verify_password(body.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Incorrect current password")
    
    hashed_password = get_password_hash(body.new_password)
    if not update_user_db(user_id, {"password_hash": hashed_password}):
        raise HTTPException(status_code=500, detail="Failed to update password")
    
    return {"message": "Password updated successfully"}

@app.patch("/users/{user_id}")
async def update_user(user_id: UUID, user_update: UserUpdate):
    updated = update_user_db(str(user_id), user_update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated

@app.delete("/users/{user_id}")
async def delete_user(user_id: UUID):
    if not delete_user_db(str(user_id)):
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted"}

# --- Brands ---

@app.post("/brands", status_code=201)
async def create_brand(brand: BrandCreate, current_user_id: str = Depends(get_current_user)):
    user_id = str(brand.user_id) if brand.user_id else current_user_id
    new_brand = create_brand_db(
        user_id, brand.name, brand.domain, brand.industry, brand.description
    )
    if not new_brand:
        raise HTTPException(status_code=500, detail="Failed to create brand")
    return new_brand

@app.get("/brands")
async def list_brands(current_user_id: str = Depends(get_current_user)):
    '''Get all brands for the current logged in user'''
    return get_user_brands_db(current_user_id)

@app.get("/users/{user_id}/brands")
async def get_user_brands(user_id: UUID):
    '''Legacy endpoint for fetching user brands by ID'''
    brands = get_user_brands_db(str(user_id))
    return brands

@app.patch("/brands/{brand_id}")
async def update_brand(brand_id: UUID, brand_update: BrandUpdate):
    updated = update_brand_db(str(brand_id), brand_update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Brand not found")
    return updated

@app.delete("/brands/{brand_id}")
async def delete_brand(brand_id: UUID):
    try:
        if not delete_brand_db(str(brand_id)):
            raise HTTPException(status_code=404, detail="Brand not found")
        return {"message": "Brand deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not delete brand: {str(e)}")

@app.get("/brands/{brand_id}/decks")
async def list_brand_decks(brand_id: UUID):
    '''Get all decks associated with a specific brand'''
    return get_brand_decks_db(str(brand_id))

@app.get("/brands/{brand_id}/prompts")
async def list_brand_prompts(brand_id: UUID):
    '''Get all prompts associated with a specific brand'''
    return get_brand_prompts_db(str(brand_id))

# --- Models ---

@app.post("/models", status_code=201)
async def create_model(model: ModelCreate):
    new_model = create_model_db(
        model.provider,
        model.model_name,
        model.external_id,
        model.pricing or {}
    )
    if not new_model:
        raise HTTPException(status_code=500, detail="Failed to create model")
    return new_model

@app.get("/models")
async def list_models():
    return get_all_models_db()

@app.patch("/models/{model_id}")
async def update_model(model_id: UUID, model_update: ModelUpdate):
    updated = update_model_db(str(model_id), model_update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Model not found")
    return updated

@app.delete("/models/{model_id}")
async def delete_model(model_id: UUID):
    if not delete_model_db(str(model_id)):
        raise HTTPException(status_code=404, detail="Model not found")
    return {"message": "Model deleted"}

# --- Regions ---

@app.post("/regions", status_code=201)
async def create_region(region: RegionCreate):
    new_region = create_region_db(region.name, region.country_code, region.region, region.city)
    if not new_region:
        raise HTTPException(status_code=500, detail="Failed to create region")
    return new_region

@app.get("/regions")
async def list_regions():
    return get_all_regions_db()

@app.patch("/regions/{region_id}")
async def update_region(region_id: UUID, region_update: RegionUpdate):
    updated = update_region_db(str(region_id), region_update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Region not found")
    return updated

@app.delete("/regions/{region_id}")
async def delete_region(region_id: UUID):
    if not delete_region_db(str(region_id)):
        raise HTTPException(status_code=404, detail="Region not found")
    return {"message": "Region deleted"}

# --- Prompts ---

@app.post("/brands/{brand_id}/prompts", status_code=201)
async def create_prompt(brand_id: UUID, prompt: PromptCreate):
    '''Create a new prompt for a specific brand.'''
    new_prompt = create_prompt_db(str(brand_id), prompt.content, prompt.notes)
    if not new_prompt:
        raise HTTPException(status_code=500, detail="Failed to create prompt")
    return new_prompt

@app.get("/prompts")
async def list_all_prompts():
    '''Get all prompts (admin/debug use only).'''
    return get_all_prompts_db()

@app.get("/prompts/{prompt_id}")
async def get_prompt(prompt_id: UUID):
    '''Get a specific prompt by ID.'''
    prompt = get_prompt_db(str(prompt_id))
    if not prompt:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return prompt

@app.patch("/prompts/{prompt_id}")
async def update_prompt(prompt_id: UUID, prompt_update: PromptUpdate):
    '''Update a prompt by ID.'''
    updated = update_prompt_db(str(prompt_id), prompt_update.dict(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Prompt not found")
    return updated

@app.delete("/prompts/{prompt_id}")
async def delete_prompt(prompt_id: UUID):
    '''Delete a prompt by ID.'''
    if not delete_prompt_db(str(prompt_id)):
        raise HTTPException(status_code=404, detail="Prompt not found")
    return {"message": "Prompt deleted"}

# --- Decks ---

@app.post("/deck")
async def create_deck(deck: DeckCreate, current_user_id: str = Depends(get_current_user)):
    '''Create a new deck.'''
    try:
        deck_data = deck.dict()
        if not deck_data.get('user_id'):
            deck_data['user_id'] = current_user_id
        new_deck = create_deck_db(deck_data)
        if not new_deck:
             raise HTTPException(status_code=500, detail="Failed to create deck")
        return {"id": new_deck.get("id"), "message": "Deck created", "data": new_deck}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/deck/{deck_id}")
async def get_deck(deck_id: UUID):
    '''Fetch a deck by ID.'''
    deck = get_deck_db(str(deck_id))
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck

@app.patch("/deck/{deck_id}")
async def update_deck(deck_id: UUID, config: DeckUpdate):
    '''Update a deck by ID.'''
    updated_deck = update_deck_db(str(deck_id), config.dict(exclude_unset=True))
    if not updated_deck:
        raise HTTPException(status_code=404, detail="Deck not found or update failed")
    return {"message": "Deck updated", "data": updated_deck}

@app.delete("/deck/{deck_id}")
async def delete_deck(deck_id: UUID):
    '''Delete a deck by ID.'''
    try:
        result = delete_deck_db(str(deck_id))
        if not result:
             raise HTTPException(status_code=404, detail="Deck not found")
        return {"message": "Deck deleted"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not delete deck: {str(e)}")

@app.get("/brands/{brand_id}/decks")
async def get_brand_decks(brand_id: UUID):
    '''Fetch all decks for a specific brand.'''
    decks = get_brand_decks_db(str(brand_id))
    return decks

# --- Instances ---

@app.get("/instances")
async def list_instances(
    deck_id: Optional[UUID] = None,
    model_id: Optional[UUID] = None,
    prompt_id: Optional[UUID] = None,
    region_id: Optional[UUID] = None
):
    '''List all instances with advanced filtering options.'''
    return get_instances_db(
        deck_id=str(deck_id) if deck_id else None,
        model_id=str(model_id) if model_id else None,
        prompt_id=str(prompt_id) if prompt_id else None,
        region_id=str(region_id) if region_id else None
    )

@app.get("/instance/{instance_id}")
async def get_instance(instance_id: UUID):
    '''Fetch detail for a specific instance.'''
    instance = get_instance_db(str(instance_id))
    if not instance:
        raise HTTPException(status_code=404, detail="Instance not found")
    return instance

@app.get("/stats/summary")
async def get_stats_summary(current_user_id: str = Depends(get_current_user)):
    '''Get dashboard statistics summary for the current user.'''
    return get_dashboard_summary_db(user_id=current_user_id)

# --- Analytics ---

@app.post("/analytics")
async def run_analytics(limit: int = 100, brand_id: Optional[UUID] = None, current_user_id: str = Depends(get_current_user)):
    """
    Finds current user's instances with empty metrics, sends them to GPT-4o-mini 
    for analysis, and saves the structured metrics back to the database.
    """
    # Cap limit to avoid HTTP timeout
    if limit > 200:
        limit = 200

    instances = get_unprocessed_instances_db(
        limit=limit, 
        user_id=current_user_id, 
        brand_id=str(brand_id) if brand_id else None
    )
    if not instances:
        return {"processed": 0, "message": "No unprocessed instances found"}

    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    async def analyze_instance(inst):
        instance_id = inst["id"]
        time_bucket = inst["time_bucket"]
        brand_name = inst["brand_name"]
        brand_domain = inst["brand_domain"]
        brand_industry = inst["brand_industry"]
        response_data = inst["response_data"]
        
        print(f"[analytics] Starting analysis for {instance_id} ({brand_name})")

        analysis_prompt = f"""You are an AI visibility analyst. Analyze the following complete AI-generated response for brand visibility, competitive presence, and source authority.

Target Brand: {brand_name}
Primary Domain: {brand_domain}
Industry: {brand_industry}

---
Complete AI Response:
{json.dumps(response_data, indent=2)}

---
Return ONLY valid JSON, no explanation, no markdown:
{{
  "brand_mentioned": boolean,
  "narrative_mention": boolean,
  "brand_position": integer or null,
  "mention_count": integer,
  "mention_context": string or null,
  "mention_intent": "recommended" | "listed" | "compared" | "neutral" | null,
  "mention_sources": [
    {{
      "source": "string",
      "url": "string",
      "is_primary_domain": boolean,
      "authority_tier": "high" | "medium" | "low"
    }}
  ],
  "competitors_mentioned": [
    {{
      "name": "string",
      "narrative": boolean,
      "position": integer or null,
      "mention_count": integer,
      "sentiment_score": float or null
    }}
  ],
  "sentiment_score": float or null,
  "all_sources": [
    {{
      "source": "string",
      "url": "string",
      "authority_tier": "high" | "medium" | "low"
    }}
  ],
  "total_brands_mentioned": integer,
  "response_word_count": integer,
  "brand_mention_density": float or null
}}

---
Rules:
- Parse the complete response yourself — extract text, citations, sources from whatever structure is present
- brand_mentioned: true if {brand_name} OR {brand_domain} appears anywhere
- brand variations: match {brand_name.lower()}, {brand_domain}, common abbreviations
- narrative_mention: true only if brand is discussed substantively, not just listed as a source
- brand_position: order of first mention across entire response (1 = first brand mentioned)
- mention_count: total number of times brand appears
- mention_context: exact sentence or phrase where brand first appears, null if not mentioned
- mention_intent: how AI is presenting the brand
    - "recommended" = AI suggests user should use/visit brand
    - "listed" = brand appears in a list without emphasis
    - "compared" = brand mentioned in comparison with others
    - "neutral" = mentioned without clear intent
- mention_sources: only sources that directly mention or link to {brand_name} or {brand_domain}
- is_primary_domain: true only if URL contains {brand_domain}
- authority_tier:
    - "high" = major publications, Wikipedia, established industry sites
    - "medium" = niche blogs, smaller publications
    - "low" = unknown sources, forums, social media
- competitors_mentioned: ALL other brands in {brand_industry} industry found in response
- competitors sentiment_score: float -1.0 to 1.0, null if not enough context
- sentiment_score: float -1.0 (very negative) to 1.0 (very positive), null if brand not mentioned
- brand_mention_density: mention_count / response_word_count, null if not mentioned
- total_brands_mentioned: count of ALL brands in response including {brand_name}
- all_sources: every unique source cited regardless of brand mention
"""
        try:
            res = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": analysis_prompt}],
                response_format={"type": "json_object"}
            )
            content = res.choices[0].message.content
            metrics = json.loads(content)
            
            print(f"[analytics] OpenAI returned metrics for {instance_id}")
            
            # Save metrics back to DB
            updated = update_instance_metrics_db(instance_id, time_bucket, metrics)
            if updated:
                print(f"[analytics] Successfully saved metrics for {instance_id}")
            else:
                print(f"[analytics] FAILED to save metrics for {instance_id}")
            
            return True
        except Exception as e:
            print(f"[analytics] Failed analyzing instance {instance_id}: {e}")
            import traceback
            traceback.print_exc()
            return False

    # Process in parallel chunks
    chunk_size = 10
    total_processed = 0
    for i in range(0, len(instances), chunk_size):
        chunk = instances[i : i + chunk_size]
        tasks = [analyze_instance(inst) for inst in chunk]
        results = await asyncio.gather(*tasks)
        total_processed += sum(1 for r in results if r is True)

    return {"processed": total_processed, "limit": limit}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
