-- Create the users table
CREATE TABLE IF NOT EXISTS users (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  password_hash TEXT NOT NULL,
  full_name TEXT,
  slack_user_id TEXT UNIQUE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create the brands table (One-to-Many: One user -> Multiple brands)
CREATE TABLE IF NOT EXISTS brands (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  name TEXT NOT NULL,
  domain TEXT,
  industry TEXT, -- This represents the "market" or sector
  description TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create the models table (LLM models independent of users)
CREATE TABLE IF NOT EXISTS models (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  provider TEXT NOT NULL, -- e.g., 'openai', 'anthropic', 'google', 'perplexity'
  model_name TEXT NOT NULL, -- e.g., 'GPT-4o Mini', 'Claude 3.5 Sonnet'
  external_id TEXT UNIQUE NOT NULL, -- API model id e.g. 'gpt-4o-mini', 'claude-3-5-sonnet-20241022'
  pricing JSONB NOT NULL DEFAULT '{}', -- Cost per 1M tokens: {"input": 0.15, "cached_input": 0.075, "output": 0.60}
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create the regions table (Geographic locations for prompt execution)
CREATE TABLE IF NOT EXISTS regions (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  name TEXT NOT NULL, -- e.g., 'California, USA'
  country_code TEXT NOT NULL, -- e.g., 'US'
  region TEXT, -- e.g., 'California'
  city TEXT, -- e.g., 'San Francisco'
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create the prompts table
CREATE TABLE IF NOT EXISTS prompts (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  brand_id UUID REFERENCES brands(id) ON DELETE CASCADE NOT NULL,
  content TEXT NOT NULL,
  notes TEXT,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create the decks table
CREATE TABLE IF NOT EXISTS decks (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  brand_id UUID REFERENCES brands(id) ON DELETE CASCADE, -- Link deck to a specific brand
  name TEXT NOT NULL, -- Name of the deck
  model_ids UUID[] NOT NULL,
  region_ids UUID[], -- Array of region IDs for geographic context
  prompt_ids UUID[] NOT NULL, -- Array of prompt IDs
  frequency INTEGER NOT NULL,
  next_execution_time TIMESTAMPTZ DEFAULT NULL,
  to_execute BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Create the instances table (Partitioned)
CREATE TABLE IF NOT EXISTS instances (
  id UUID DEFAULT gen_random_uuid(),
  
  -- Hypercube dimensions
  time_bucket TIMESTAMPTZ NOT NULL, -- Monthly bucket for partitioning (e.g., '2026-01-01')
  initiated_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ,
  
  user_id UUID REFERENCES users(id) ON DELETE CASCADE NOT NULL,
  brand_id UUID REFERENCES brands(id) ON DELETE CASCADE NOT NULL,
  deck_id UUID REFERENCES decks(id) ON DELETE CASCADE NOT NULL,
  prompt_id UUID REFERENCES prompts(id) ON DELETE CASCADE NOT NULL,
  model_id UUID REFERENCES models(id) ON DELETE CASCADE NOT NULL,
  region_id UUID REFERENCES regions(id) ON DELETE SET NULL,
  
  -- Denormalized dims (for fast queries)
  brand_name TEXT NOT NULL,
  deck_name TEXT NOT NULL,
  model_name TEXT NOT NULL,
  prompt_content TEXT NOT NULL,
  region_name TEXT,
  
  -- Raw data (immutable)
  response_data JSONB NOT NULL,
  
  -- Computed metrics (mutable, can reprocess)
  metrics JSONB,
  
  PRIMARY KEY (id, time_bucket)
) PARTITION BY RANGE (time_bucket);

-- Create a default partition to start with
CREATE TABLE IF NOT EXISTS instances_default PARTITION OF instances DEFAULT;

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_brands_user_id ON brands(user_id);
CREATE INDEX IF NOT EXISTS idx_decks_user_id ON decks(user_id);
CREATE INDEX IF NOT EXISTS idx_decks_brand_id ON decks(brand_id);
CREATE INDEX IF NOT EXISTS idx_decks_model_ids ON decks USING GIN (model_ids);
CREATE INDEX IF NOT EXISTS idx_decks_region_ids ON decks USING GIN (region_ids);
CREATE INDEX IF NOT EXISTS idx_decks_prompt_ids ON decks USING GIN (prompt_ids);
CREATE INDEX IF NOT EXISTS idx_models_provider ON models(provider);
CREATE INDEX IF NOT EXISTS idx_prompts_brand_id ON prompts(brand_id);
CREATE INDEX IF NOT EXISTS idx_prompts_content ON prompts(content);

-- Instance specific Hypercube index
CREATE INDEX IF NOT EXISTS idx_instances_hypercube ON instances(
  time_bucket, brand_id, model_id, prompt_id
);
CREATE INDEX IF NOT EXISTS idx_instances_response ON instances USING GIN (response_data);
CREATE INDEX IF NOT EXISTS idx_instances_metrics ON instances USING GIN (metrics);
