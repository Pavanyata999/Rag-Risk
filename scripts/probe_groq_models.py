import os
import json
import urllib.request
from pathlib import Path

# Load from .env or docs/paper/.env without ever printing/logging the key
env_paths = [Path('.env'), Path('docs/paper/.env')]
for p in env_paths:
    if p.exists():
        for line in p.read_text().splitlines():
            if 'TOLLGATERAG_LLM_API_KEY' in line and '=' in line:
                k = line.split('=', 1)[1].strip().strip('\"\' ')
                os.environ['TOLLGATERAG_LLM_API_KEY'] = k

key = os.environ.get('TOLLGATERAG_LLM_API_KEY', '')
if not key:
    print('KEY NOT FOUND')
    exit(1)

req = urllib.request.Request(
    'https://api.groq.com/openai/v1/models',
    headers={'Authorization': f'Bearer {key}'}
)
try:
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        ids = sorted([m['id'] for m in data.get('data', [])])
        print(f'SUCCESS: Found {len(ids)} models on Groq:')
        for mid in ids:
            print(f'  - {mid}')
        os.makedirs('logs', exist_ok=True)
        with open('logs/groq_models_available.json', 'w') as f:
            json.dump({'date': '2026-10-12', 'endpoint': 'https://api.groq.com/openai/v1/models', 'models': ids}, f, indent=2)
        print('Saved to logs/groq_models_available.json')
except Exception as e:
    print(f'ERROR: {e}')
