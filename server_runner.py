import sys
import waitress
import uvicorn

def run():
    """Run the appropriate server based on whether the application is frozen."""
    if getattr(sys, 'frozen', False):
        # Use waitress for production (bundled) mode
        waitress.serve()
    else:
        # Use uvicorn for development mode
        uvicorn.run()