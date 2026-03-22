import json, os, shutil, datetime
CONFIG_FILE = "config.json"
BACKUP_DIR = "config_backups"

DEFAULT_CONFIG = {
    "galaxy_threshold": 75, "volume_multiplier": 1.5, "rug_score_min": 80,
    "maker_only": True, "flash_loan_enabled": False, "daily_loss_max": 1.0,
    "preset": "default", "api_tier": "free", "battery_saver": False
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f: return json.load(f)
    save_config(DEFAULT_CONFIG)
    return DEFAULT_CONFIG

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f: json.dump(cfg, f, indent=2)
    os.makedirs(BACKUP_DIR, exist_ok=True)
    shutil.copy(CONFIG_FILE, f"{BACKUP_DIR}/config_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
