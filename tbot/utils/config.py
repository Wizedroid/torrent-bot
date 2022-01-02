import yaml
import os

def load_config(path):
    if os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    else:
        print(f"Config file not found. ({path})!")
