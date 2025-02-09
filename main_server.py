from fastapi import FastAPI, Depends, HTTPException, Request
import csv
import os
import secrets
import json
from datetime import datetime, timedelta
from get_val import get_val, generate_game_params

app = FastAPI()

CSV_FILE = "api_keys.csv"
MAX_REQUESTS = 10

# Load API keys from CSV


def load_api_keys():
    api_keys = {}
    if os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode="r") as file:
            reader = csv.reader(file)
            for row in reader:
                token, username, expiry, num_games, params, requests = row
                api_keys[token] = {
                    "username": username,
                    "expiry": datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S"),
                    "num_games": int(num_games),
                    "params": json.loads(params),
                    "requests": int(requests)
                }
    return api_keys

# Save API keys to CSV


def save_api_keys(api_keys):
    with open(CSV_FILE, mode="w", newline="") as file:
        writer = csv.writer(file)
        for token, data in api_keys.items():
            writer.writerow([
                token,
                data["username"],
                data["expiry"].strftime("%Y-%m-%d %H:%M:%S"),
                data["num_games"],
                json.dumps(data["params"]),
                data["requests"]
            ])


VALID_API_KEYS = load_api_keys()

# Middleware to verify API key and enforce rate limiting


def verify_api_key(request: Request):
    api_key = request.headers.get("key")
    username = request.headers.get("name")

    if not api_key or api_key not in VALID_API_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API Key")

    user_data = VALID_API_KEYS[api_key]

    if user_data["username"] != username:
        raise HTTPException(status_code=403, detail="Unauthorized Access")

    if datetime.utcnow() > user_data["expiry"]:
        del VALID_API_KEYS[api_key]
        save_api_keys(VALID_API_KEYS)
        raise HTTPException(status_code=403, detail="API Key expired")

    if user_data["requests"] >= MAX_REQUESTS:
        raise HTTPException(status_code=429, detail="Request limit exceeded")

    user_data["requests"] += 1
    save_api_keys(VALID_API_KEYS)
    return api_key


@app.post("/")
def f(input: dict, api_key: str = Depends(verify_api_key)):
    """Process user request based on stored API key parameters."""
    token_data = VALID_API_KEYS[api_key]
    params = token_data["params"]

    game = input.get("game")
    if game < 0 or game >= token_data["num_games"]:
        raise HTTPException(status_code=400, detail="Invalid game index.")

    result = get_val(
        game, params["means"], params["std_devs"], params["distributions"][game])
    return {"point": result}


@app.post("/generate-token")
def generate_token(request: Request):
    """Generate a unique API token with random game configurations."""
    username = request.headers.get("Username")
    if not username:
        raise HTTPException(
            status_code=400, detail="Username is required in the header.")

    new_token = secrets.token_hex(16)
    num_games = secrets.randbelow(5) + 3  # Number of games (3 to 7)
    params = generate_game_params(num_games)
    expiry = datetime.utcnow() + timedelta(days=1)

    VALID_API_KEYS[new_token] = {
        "username": username,
        "expiry": expiry,
        "num_games": num_games,
        "params": params,
        "requests": 0
    }
    save_api_keys(VALID_API_KEYS)

    return {
        "api_key": new_token,
        "expiry": expiry.strftime("%Y-%m-%d %H:%M:%S"),
        "num_games": num_games
    }


@app.get("/admin/view-keys")
def view_keys(admin_key: str):
    """Admin-only route to view all stored API keys and configurations."""
    if admin_key != "admin-secret":
        raise HTTPException(status_code=403, detail="Unauthorized Access")

    return VALID_API_KEYS
