import os
from pathlib import Path
from dotenv import load_dotenv

print("=== Environment Loading Debug ===")
print(f"Current working directory: {os.getcwd()}")

# Test the path resolution from config.py
config_file = Path(__file__).parent / "app" / "config.py"
dotenv_path = config_file.parent.parent / ".env"
print(f"Config file: {config_file}")
print(f"Expected .env path: {dotenv_path}")
print(f"Expected .env exists: {dotenv_path.exists()}")

# Check if there are other .env files
root_dir = Path(__file__).parent.parent
print(f"\nRoot directory: {root_dir}")

# Look for all .env files
for env_file in root_dir.rglob(".env"):
    print(f"Found .env file: {env_file}")

# Test loading the specific .env file
print(f"\nLoading .env from: {dotenv_path}")
if dotenv_path.exists():
    load_dotenv(dotenv_path)
    print(f"OPENAI_API_KEY loaded: {os.getenv('OPENAI_API_KEY', 'NOT_FOUND')[:20]}...")
else:
    print("Expected .env file not found!")

# Test what happens if we don't specify a path (default behavior)
print(f"\nTesting default dotenv behavior...")
load_dotenv()  # This will search current directory and parents
print(f"OPENAI_API_KEY after default load: {os.getenv('OPENAI_API_KEY', 'NOT_FOUND')[:20]}...") 