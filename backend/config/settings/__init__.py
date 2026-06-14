from pathlib import Path
from split_settings.tools import optional, include
from dotenv import load_dotenv

env_file = Path(__file__).resolve().parent.parent.parent.parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

env = __import__("os").environ.get("DJANGO_ENV", "development")

component_files = [
    "base.py",
]

if env == "production":
    component_files.append("production.py")
else:
    component_files.append("development.py")
    component_files.append(optional("local.py"))

include(*component_files)
