import os
import requests

icons = {
    "warning": "triangle-alert",
    "info": "info",
    "urgent": "siren",
    "bell": "bell",
    "wheat": "wheat",
    "map": "map",
    "brain": "brain",
    "calendar": "calendar",
    "message": "message-circle",
    "compass": "compass",
    "bot": "bot"
}

os.makedirs("assets", exist_ok=True)

for name, lucide_name in icons.items():
    url = f"https://raw.githubusercontent.com/lucide-icons/lucide/main/icons/{lucide_name}.svg"
    resp = requests.get(url)
    if resp.status_code == 200:
        with open(f"assets/{name}.svg", "w") as f:
            f.write(resp.text)
        print(f"Downloaded {name}.svg")
    else:
        print(f"Failed to download {name}.svg")
