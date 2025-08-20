import traceback
import sys

print('Python:', sys.version)
try:
    from app import create_app
    print('Imported create_app successfully')
    app = create_app()
    print('App created successfully')
except Exception:
    print('ERROR DURING APP CREATION:')
    traceback.print_exc()
    sys.exit(1)
