#!/usr/bin/env python3
"""
Simple test server for Step 11: Base Templates & Styling
This server only serves static files and templates without the full application dependencies.
"""

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn

# Create FastAPI app
app = FastAPI(title="Template Test Server")

# Set up static files and templates
static_dir = Path("web/static")
templates_dir = Path("web/templates")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
templates = Jinja2Templates(directory=str(templates_dir))

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Template Test Server",
        "test_page": "/test"
    }

@app.get("/test")
async def test_page(request: Request):
    """Test page for base templates and styling."""
    return templates.TemplateResponse("test.html", {"request": request})

if __name__ == "__main__":
    print("Starting Template Test Server...")
    print("Visit http://localhost:8001/test to see the styling test page")
    uvicorn.run(app, host="127.0.0.1", port=8001)