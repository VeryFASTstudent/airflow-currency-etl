"""Generate local-only credentials without printing or overwriting them."""
from pathlib import Path
import secrets

root = Path(__file__).resolve().parents[1]
path = root / '.env'
if path.exists():
    raise SystemExit('.env already exists; keep it or move it before generating a new file.')
password = secrets.token_hex(24)
viewer_password = secrets.token_hex(24)
body = '\n'.join([
    'MONGO_ROOT_USERNAME=etl_admin',
    f'MONGO_ROOT_PASSWORD={password}',
    f'MONGO_URI=mongodb://etl_admin:{password}@mongodb:27017/?authSource=admin',
    'MONGO_DATABASE=currency_etl', 'MONGO_COLLECTION=exchange_rates',
    'ME_USERNAME=viewer', f'ME_PASSWORD={viewer_password}',
    'FX_BASE=EUR', 'FX_QUOTES=USD,GBP,JPY', '',
])
with path.open('x') as stream:
    stream.write(body)
path.chmod(0o600)
print('Created .env with generated credentials. Keep this file private.')
