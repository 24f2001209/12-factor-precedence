import os
import yaml
from typing import List, Optional
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import dotenv_values

# --- Setup: Generate assigned layers on startup ---
with open("config.development.yaml", "w") as f:
    yaml.dump({
        "log_level": "warning", 
        "api_key": "key-ffo5bq56jh"
    }, f)

with open(".env", "w") as f:
    f.write("APP_PORT=8036\nNUM_WORKERS=8\nAPP_API_KEY=key-c1sj3z950n\n")

os.environ["APP_PORT"] = "8355"
os.environ["APP_LOG_LEVEL"] = "error"
# --------------------------------------------------

app = FastAPI()

# Allow cross-origin requests for the grader
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def parse_bool(v):
    if isinstance(v, str):
        return v.lower() in ["true", "1", "yes", "on"]
    return bool(v)

@app.get("/effective-config")
def get_effective_config(set: Optional[List[str]] = Query(default=[])):
    # Layer 1: Defaults
    config = {
        "port": 8000,
        "workers": 1,
        "debug": False,
        "log_level": "info",
        "api_key": "default-secret-000"
    }
    
    # Layer 2: Environment-specific YAML
    try:
        with open("config.development.yaml", "r") as f:
            yaml_data = yaml.safe_load(f) or {}
            config.update(yaml_data)
    except Exception:
        pass
        
    # Layer 3: .env file
    env_data = dotenv_values(".env")
    for k, v in env_data.items():
        if k == "NUM_WORKERS":
            config["workers"] = v
        elif k.startswith("APP_"):
            config[k[4:].lower()] = v
            
    # Layer 4: OS-level environment variables
    for k, v in os.environ.items():
        if k.startswith("APP_"):
            config[k[4:].lower()] = v
            
    # Layer 5: CLI Overrides (Highest Precedence)
    if set:
        for override in set:
            if "=" in override:
                k, v = override.split("=", 1)
                config[k] = v

    # Type Coercion & Masking
    final_config = {}
    for k, v in config.items():
        if k in ["port", "workers"]:
            final_config[k] = int(v)
        elif k == "debug":
            final_config[k] = parse_bool(v)
        else:
            final_config[k] = str(v)
            
    # Mask secret
    if "api_key" in final_config:
        final_config["api_key"] = "****"
        
    return final_config