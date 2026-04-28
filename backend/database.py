import os
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor, Json
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    # Register UUIDs globally for this connection so arrays are handled correctly
    psycopg2.extras.register_uuid(conn_or_curs=conn)
    return conn

def _ensure_uuid_list(val):
    """Helper to ensure we have a list of strings, even if Postgres returns a string-formatted array."""
    if isinstance(val, str):
        # Handle "{uuid1,uuid2}" format
        clean = val.strip('{}')
        return [x.strip() for x in clean.split(',')] if clean else []
    return val if isinstance(val, list) else []

def _to_str(val):
    if val is None: return None
    return str(val)

def create_deck_db(data: dict):
    # Updated to use name, brand_id, model_ids, region_ids, user_id, and prompt_ids
    query = """
    INSERT INTO decks (user_id, brand_id, name, model_ids, region_ids, prompt_ids, frequency, to_execute)
    VALUES (%s, %s, %s, %s::uuid[], %s::uuid[], %s::uuid[], %s, %s)
    RETURNING *;
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (
            _to_str(data.get("user_id") or data.get("userId")),
            _to_str(data.get("brand_id") or data.get("brandId")),
            data.get("name"),
            [_to_str(mid) for mid in data.get("model_ids", [])] if data.get("model_ids") else [],
            [_to_str(rid) for rid in data.get("region_ids", [])] if data.get("region_ids") else None,
            [_to_str(pid) for pid in data.get("prompt_ids", [])] if data.get("prompt_ids") else [],
            data.get("frequency"),
            data.get("to_execute", True)
        ))
        new_deck = cur.fetchone()
        conn.commit()
        return dict(new_deck) if new_deck else None
    finally:
        conn.close()

def get_deck_db(deck_id: str):
    query = "SELECT * FROM decks WHERE id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (deck_id,))
        deck = cur.fetchone()
        return dict(deck) if deck else None
    finally:
        conn.close()

def get_brand_decks_db(brand_id: str):
    query = "SELECT * FROM decks WHERE brand_id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (brand_id,))
        decks = cur.fetchall()
        
        results = []
        for d in decks:
            deck_dict = dict(d)
            deck_dict['model_ids'] = _ensure_uuid_list(deck_dict.get('model_ids'))
            deck_dict['region_ids'] = _ensure_uuid_list(deck_dict.get('region_ids'))
            deck_dict['prompt_ids'] = _ensure_uuid_list(deck_dict.get('prompt_ids'))
            results.append(deck_dict)
        return results
    finally:
        conn.close()

def update_deck_db(deck_id: str, data: dict):
    # Construct dynamic update query
    fields = []
    values = []
    for key, value in data.items():
        if key == "id": continue
        # Handle field renaming or specific mappings if necessary
        fields.append(f'"{key}" = %s')
        values.append(value)
    
    if not fields:
        return None
    
    values.append(deck_id)
    query = f"UPDATE decks SET {', '.join(fields)} WHERE id = %s RETURNING *;"
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(values))
        updated_deck = cur.fetchone()
        conn.commit()
        return dict(updated_deck) if updated_deck else None
    finally:
        conn.close()

def delete_deck_db(deck_id: str):
    query = "DELETE FROM decks WHERE id = %s RETURNING id;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (deck_id,))
        result = cur.fetchone()
        conn.commit()
        return result if result else None
    finally:
        conn.close()

def fetch_active_decks_db():
    query = "SELECT * FROM decks WHERE to_execute = True;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        decks = cur.fetchall()
        results = []
        for d in decks:
            deck_dict = dict(d)
            deck_dict['model_ids'] = _ensure_uuid_list(deck_dict.get('model_ids'))
            deck_dict['region_ids'] = _ensure_uuid_list(deck_dict.get('region_ids'))
            deck_dict['prompt_ids'] = _ensure_uuid_list(deck_dict.get('prompt_ids'))
            results.append(deck_dict)
        return results
    finally:
        conn.close()

def get_all_decks_db():
    """Admin: get every deck regardless of to_execute status."""
    query = "SELECT * FROM decks ORDER BY created_at DESC;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        decks = cur.fetchall()
        results = []
        for d in decks:
            deck_dict = dict(d)
            deck_dict['model_ids'] = _ensure_uuid_list(deck_dict.get('model_ids'))
            deck_dict['region_ids'] = _ensure_uuid_list(deck_dict.get('region_ids'))
            deck_dict['prompt_ids'] = _ensure_uuid_list(deck_dict.get('prompt_ids'))
            results.append(deck_dict)
        return results
    finally:
        conn.close()

def batch_update_execution_time_db(updates: list):
    if not updates:
        return
    
    # Use UPSERT logic
    query = """
    INSERT INTO decks (id, user_id, brand_id, name, model_ids, region_ids, prompt_ids, frequency, next_execution_time)
    VALUES (%s, %s, %s, %s, %s::uuid[], %s::uuid[], %s::uuid[], %s, %s)
    ON CONFLICT (id) DO UPDATE SET
        next_execution_time = EXCLUDED.next_execution_time;
    """
    
    conn = get_connection()
    try:
        cur = conn.cursor()
        for update in updates:
            cur.execute(query, (
                _to_str(update.get("id")),
                _to_str(update.get("user_id") or update.get("userId")),
                _to_str(update.get("brand_id") or update.get("brandId")),
                update.get("name"),
                [_to_str(mid) for mid in update.get("model_ids", [])] if update.get("model_ids") else [],
                [_to_str(rid) for rid in update.get("region_ids", [])] if update.get("region_ids") else None,
                [_to_str(pid) for pid in update.get("prompt_ids", [])] if update.get("prompt_ids") else [],
                update.get("frequency"),
                update.get("next_execution_time")
            ))
        conn.commit()
    finally:
        conn.close()

def reset_execution_times_db():
    query = "UPDATE decks SET next_execution_time = NULL WHERE id IS NOT NULL;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        return True
    finally:
        conn.close()

def get_all_users_db():
    query = "SELECT * FROM users ORDER BY created_at DESC;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        users = cur.fetchall()
        return [dict(u) for u in users] if users else []
    finally:
        conn.close()

# --- User Functions ---
def create_user_db(email: str, password_hash: str, full_name: str = None):
    query = "INSERT INTO users (email, password_hash, full_name) VALUES (%s, %s, %s) RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (email, password_hash, full_name))
        user = cur.fetchone()
        conn.commit()
        return dict(user) if user else None
    finally:
        conn.close()

def get_user_by_email(email: str):
    query = "SELECT * FROM users WHERE email = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (email,))
        user = cur.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def get_user_db(user_id: str):
    query = "SELECT * FROM users WHERE id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (user_id,))
        user = cur.fetchone()
        return dict(user) if user else None
    finally:
        conn.close()

def update_user_db(user_id: str, data: dict):
    fields = []
    values = []
    for key, value in data.items():
        if key == "id": continue
        fields.append(f'"{key}" = %s')
        values.append(value)
    if not fields: return None
    values.append(user_id)
    query = f"UPDATE users SET {', '.join(fields)} WHERE id = %s RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(values))
        updated = cur.fetchone()
        conn.commit()
        return dict(updated) if updated else None
    finally:
        conn.close()

def delete_user_db(user_id: str):
    query = "DELETE FROM users WHERE id = %s RETURNING id;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (user_id,))
        result = cur.fetchone()
        conn.commit()
        return result if result else None
    finally:
        conn.close()

# --- Brand Functions ---
def create_brand_db(user_id: str, name: str, domain: str = None, industry: str = None, description: str = None):
    query = """
    INSERT INTO brands (user_id, name, domain, industry, description) 
    VALUES (%s, %s, %s, %s, %s) 
    RETURNING *;
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (user_id, name, domain, industry, description))
        brand = cur.fetchone()
        conn.commit()
        return dict(brand) if brand else None
    finally:
        conn.close()

def get_all_brands_db():
    """Admin: get every brand across all users."""
    query = "SELECT * FROM brands ORDER BY created_at DESC;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        brands = cur.fetchall()
        return [dict(b) for b in brands] if brands else []
    finally:
        conn.close()

def get_user_brands_db(user_id: str):
    query = "SELECT * FROM brands WHERE user_id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (user_id,))
        brands = cur.fetchall()
        return [dict(b) for b in brands] if brands else []
    finally:
        conn.close()

def get_brand_db(brand_id: str):
    query = "SELECT * FROM brands WHERE id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (brand_id,))
        brand = cur.fetchone()
        return dict(brand) if brand else None
    finally:
        conn.close()

def update_brand_db(brand_id: str, data: dict):
    fields = []
    values = []
    for key, value in data.items():
        if key == "id": continue
        fields.append(f'"{key}" = %s')
        values.append(value)
    if not fields: return None
    values.append(brand_id)
    query = f"UPDATE brands SET {', '.join(fields)} WHERE id = %s RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(values))
        updated = cur.fetchone()
        conn.commit()
        return dict(updated) if updated else None
    finally:
        conn.close()

def delete_brand_db(brand_id: str):
    query = "DELETE FROM brands WHERE id = %s RETURNING id;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (brand_id,))
        result = cur.fetchone()
        conn.commit()
        return result if result else None
    finally:
        conn.close()

# --- Model Functions ---
def create_model_db(provider: str, model_name: str, external_id: str, pricing: dict = None):
    query = """
    INSERT INTO models (provider, model_name, external_id, pricing)
    VALUES (%s, %s, %s, %s)
    RETURNING *;
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (provider, model_name, external_id, Json(pricing or {})))
        model = cur.fetchone()
        conn.commit()
        return dict(model) if model else None
    finally:
        conn.close()

def get_all_models_db():
    query = "SELECT * FROM models;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        models = cur.fetchall()
        return [dict(m) for m in models] if models else []
    finally:
        conn.close()

def get_model_db(model_id: str):
    query = "SELECT * FROM models WHERE id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (model_id,))
        model = cur.fetchone()
        return dict(model) if model else None
    finally:
        conn.close()

def update_model_db(model_id: str, data: dict):
    fields = []
    values = []
    for key, value in data.items():
        if key == "id": continue
        fields.append(f'"{key}" = %s')
        # Serialize pricing dict as JSONB
        values.append(Json(value) if key == "pricing" else value)
    if not fields: return None
    values.append(model_id)
    query = f"UPDATE models SET {', '.join(fields)} WHERE id = %s RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(values))
        updated = cur.fetchone()
        conn.commit()
        return dict(updated) if updated else None
    finally:
        conn.close()

def delete_model_db(model_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        # 1. Clean up Decks array
        cur.execute("UPDATE decks SET model_ids = array_remove(model_ids, %s::uuid) WHERE %s::uuid = ANY(model_ids)", (model_id, model_id))
        
        # 2. Delete Instances
        cur.execute("DELETE FROM instances WHERE model_id = %s", (model_id,))
        
        # 3. Delete Model
        cur.execute("DELETE FROM models WHERE id = %s RETURNING id;", (model_id,))
        result = cur.fetchone()
        conn.commit()
        return result if result else None
    except Exception as e:
        print(f"DATABASE ERROR in delete_model_db: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Region Functions ---
def create_region_db(name: str, country_code: str, region: str = None, city: str = None):
    query = """
    INSERT INTO regions (name, country_code, region, city) 
    VALUES (%s, %s, %s, %s) 
    RETURNING *;
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (name, country_code, region, city))
        res = cur.fetchone()
        conn.commit()
        return dict(res) if res else None
    finally:
        conn.close()

def get_all_regions_db():
    query = "SELECT * FROM regions;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        regions = cur.fetchall()
        return [dict(r) for r in regions] if regions else []
    finally:
        conn.close()

def get_region_db(region_id: str):
    query = "SELECT * FROM regions WHERE id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (region_id,))
        region = cur.fetchone()
        return dict(region) if region else None
    finally:
        conn.close()

def update_region_db(region_id: str, data: dict):
    fields = []
    values = []
    for key, value in data.items():
        if key == "id": continue
        fields.append(f'"{key}" = %s')
        values.append(value)
    if not fields: return None
    values.append(region_id)
    query = f"UPDATE regions SET {', '.join(fields)} WHERE id = %s RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(values))
        updated = cur.fetchone()
        conn.commit()
        return dict(updated) if updated else None
    finally:
        conn.close()

def delete_region_db(region_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        # 1. Clean up Decks array
        cur.execute("UPDATE decks SET region_ids = array_remove(region_ids, %s::uuid) WHERE %s::uuid = ANY(region_ids)", (region_id, region_id))
        
        # 2. Delete Instances
        cur.execute("DELETE FROM instances WHERE region_id = %s", (region_id,))
        
        # 3. Delete Region
        cur.execute("DELETE FROM regions WHERE id = %s RETURNING id;", (region_id,))
        result = cur.fetchone()
        conn.commit()
        return result if result else None
    except Exception as e:
        print(f"DATABASE ERROR in delete_region_db: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Prompt Functions ---
def create_prompt_db(brand_id: str, content: str, notes: str = None):
    query = "INSERT INTO prompts (brand_id, content, notes) VALUES (%s, %s, %s) RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (brand_id, content, notes))
        res = cur.fetchone()
        conn.commit()
        return dict(res) if res else None
    finally:
        conn.close()

def get_all_prompts_db():
    """Get all prompts (admin use only - deprecated, use get_brand_prompts_db instead)"""
    query = "SELECT * FROM prompts;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query)
        prompts = cur.fetchall()
        return [dict(p) for p in prompts] if prompts else []
    finally:
        conn.close()

def get_brand_prompts_db(brand_id: str):
    """Get all prompts for a specific brand"""
    query = "SELECT * FROM prompts WHERE brand_id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (brand_id,))
        prompts = cur.fetchall()
        return [dict(p) for p in prompts] if prompts else []
    finally:
        conn.close()

def get_prompt_db(prompt_id: str):
    query = "SELECT * FROM prompts WHERE id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (prompt_id,))
        res = cur.fetchone()
        return dict(res) if res else None
    finally:
        conn.close()

def update_prompt_db(prompt_id: str, data: dict):
    fields = []
    values = []
    for key, value in data.items():
        if key == "id": continue
        fields.append(f'"{key}" = %s')
        values.append(value)
    if not fields: return None
    values.append(prompt_id)
    query = f"UPDATE prompts SET {', '.join(fields)} WHERE id = %s RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(values))
        updated = cur.fetchone()
        conn.commit()
        return dict(updated) if updated else None
    finally:
        conn.close()

def delete_prompt_db(prompt_id: str):
    conn = get_connection()
    try:
        cur = conn.cursor()
        # 1. Clean up Decks (arrays don't support FKs or Cascade)
        cur.execute("UPDATE decks SET prompt_ids = array_remove(prompt_ids, %s::uuid) WHERE %s::uuid = ANY(prompt_ids)", (prompt_id, prompt_id))
        
        # 2. Manually delete Instances linked to this prompt
        # (Using a manual delete as the cascade on partitioned instances might be failing in some PG versions/configs)
        cur.execute("DELETE FROM instances WHERE prompt_id = %s", (prompt_id,))
        
        # 3. Finally delete the prompt
        cur.execute("DELETE FROM prompts WHERE id = %s RETURNING id;", (prompt_id,))
        result = cur.fetchone()
        conn.commit()
        return result if result else None
    except Exception as e:
        print(f"DATABASE ERROR in delete_prompt_db: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()

# --- Instance Functions ---
def create_instance_db(data: dict):
    query = """
    INSERT INTO instances (
        time_bucket, initiated_at, completed_at, 
        user_id, brand_id, deck_id, prompt_id, model_id, region_id,
        brand_name, deck_name, model_name, prompt_content, region_name,
        response_data, metrics
    ) VALUES (
        %s, %s, %s, 
        %s, %s, %s, %s, %s, %s,
        %s, %s, %s, %s, %s,
        %s, %s
    ) RETURNING *;
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (
            data.get("time_bucket"),
            data.get("initiated_at"),
            data.get("completed_at"),
            str(data.get("user_id")) if data.get("user_id") else None,
            str(data.get("brand_id")) if data.get("brand_id") else None,
            str(data.get("deck_id")) if data.get("deck_id") else None,
            str(data.get("prompt_id")) if data.get("prompt_id") else None,
            str(data.get("model_id")) if data.get("model_id") else None,
            str(data.get("region_id")) if data.get("region_id") else None,
            data.get("brand_name"),
            data.get("deck_name"),
            data.get("model_name"),
            data.get("prompt_content"),
            data.get("region_name"),
            Json(data.get("response_data", {})),
            Json(data.get("metrics", {}))
        ))
        new_instance = cur.fetchone()
        conn.commit()
        return dict(new_instance) if new_instance else None
    finally:
        conn.close()

def get_instances_db(
    deck_id: str = None, 
    model_id: str = None, 
    prompt_id: str = None, 
    region_id: str = None
):
    query = "SELECT * FROM instances"
    filters = []
    params = []

    if deck_id:
        filters.append("deck_id = %s")
        params.append(str(deck_id))
    if model_id:
        filters.append("model_id = %s")
        params.append(str(model_id))
    if prompt_id:
        filters.append("prompt_id = %s")
        params.append(str(prompt_id))
    if region_id:
        filters.append("region_id = %s")
        params.append(str(region_id))

    if filters:
        query += " WHERE " + " AND ".join(filters)
    
    query += " ORDER BY initiated_at DESC;"
        
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(params) if params else None)
        instances = cur.fetchall()
        return [dict(i) for i in instances] if instances else []
    finally:
        conn.close()

def get_instance_db(instance_id: str):
    query = "SELECT * FROM instances WHERE id = %s;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (instance_id,))
        res = cur.fetchone()
        if res:
            data = dict(res)
            # Helper to extract text for the frontend
            response_data = data.get('response_data', {})
            data['response_text'] = response_data.get('output_text', '') or str(response_data)
            data['status'] = 'completed' if data.get('completed_at') else 'pending'
            return data
        return None
    finally:
        conn.close()

def get_dashboard_summary_db(user_id: str = None):
    conn = get_connection()
    try:
        cur = conn.cursor()
        
        # 1. Total Brands
        q1 = "SELECT COUNT(*) as count FROM brands"
        params = []
        if user_id:
            q1 += " WHERE user_id = %s"
            params.append(user_id)
        cur.execute(q1, tuple(params))
        total_brands = cur.fetchone()['count']
        
        # 2. Active Decks
        q2 = "SELECT COUNT(*) as count FROM decks WHERE to_execute = TRUE"
        params = []
        if user_id:
            q2 += " AND user_id = %s"
            params.append(user_id)
        cur.execute(q2, tuple(params))
        active_decks = cur.fetchone()['count']
        
        # 3. Total Prompts
        q3 = "SELECT COUNT(*) as count FROM prompts"
        params = []
        if user_id:
            q3 += " WHERE brand_id IN (SELECT id FROM brands WHERE user_id = %s)"
            params.append(user_id)
        cur.execute(q3, tuple(params))
        total_prompts = cur.fetchone()['count']
        
        # 4. Execution Trend (Last 7 days)
        trend_query = """
            SELECT date_trunc('day', initiated_at) as day, COUNT(*) as count 
            FROM instances 
            WHERE initiated_at > CURRENT_DATE - INTERVAL '7 days'
        """
        trend_params = []
        if user_id:
            trend_query += " AND user_id = %s"
            trend_params.append(user_id)
        
        trend_query += " GROUP BY 1 ORDER BY 1;"
        
        cur.execute(trend_query, tuple(trend_params))
        trend_data = cur.fetchall()
        trend = [{"day": str(row['day'].date()), "count": row['count']} for row in trend_data]
        
        return {
            "total_brands": total_brands,
            "active_decks": active_decks,
            "total_prompts": total_prompts,
            "execution_trend": trend
        }
    finally:
        conn.close()

def get_unprocessed_instances_db(limit=50, user_id=None, brand_id=None):
    """Fetch instances with missing metrics, including brand info."""
    params = []
    filters = []
    if user_id:
        filters.append("i.user_id = %s")
        params.append(str(user_id))
    
    if brand_id:
        filters.append("i.brand_id = %s")
        params.append(str(brand_id))
        
    where_clause = " AND ".join(filters) if filters else "1=1"
    
    params.append(limit)
    
    query = f"""
    SELECT i.*, b.domain as brand_domain, b.industry as brand_industry
    FROM instances i
    JOIN brands b ON i.brand_id = b.id
    WHERE (i.metrics IS NULL OR i.metrics = '{{}}'::jsonb)
    AND {where_clause}
    LIMIT %s;
    """
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, tuple(params))
        instances = cur.fetchall()
        return [dict(i) for i in instances] if instances else []
    finally:
        conn.close()

def update_instance_metrics_db(instance_id: str, time_bucket, metrics: dict):
    """Update metrics for a specific instance."""
    query = "UPDATE instances SET metrics = %s WHERE id = %s AND time_bucket = %s RETURNING *;"
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, (Json(metrics), str(instance_id), time_bucket))
        updated = cur.fetchone()
        conn.commit()
        return dict(updated) if updated else None
    finally:
        conn.close()
