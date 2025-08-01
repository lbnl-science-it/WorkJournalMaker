# Technical Specification: FastAPI Desktop Application Packaging

## 1. Project Overview

This document outlines the technical specification for packaging a self-contained FastAPI web application into a desktop installable for macOS and Windows. The final executable will start a local web server and open the application in the user's default web browser.

## 2. Core Technology Stack

- **Packaging Tool:** `PyInstaller` will be used to bundle the Python application and its dependencies into a single executable.
- **Web Server:** `uvicorn` will serve the FastAPI application.
- **Browser Interaction:** The `webbrowser` module in Python's standard library will be used to open the application URL.
- **Build Environment:** The build will be standardized on **Python 3.11**.

## 3. Implementation Details

### 3.1. Entry Point Script: `server_runner.py`

A new Python script, `server_runner.py`, will be created at the root of the project. This script will serve as the entry point for the `PyInstaller` build.

**Responsibilities:**

1.  **Start `uvicorn` Server:** The script will launch the FastAPI application using `uvicorn` in a separate thread to prevent blocking.
2.  **Server Initialization Delay:** A short delay will be implemented to ensure the server is fully running before attempting to open the browser.
3.  **Open Browser:** The script will call `webbrowser.open()` to launch `http://127.0.0.1:8000` in the user's default browser.

**Example `server_runner.py`:**

```python
import threading
import time
import uvicorn
import webbrowser
from web.app import app

def run_server():
    uvicorn.run(app, host="127.0.0.1", port=8000)

if __name__ == "__main__":
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    time.sleep(2)  # Wait for server to start
    webbrowser.open("http://127.0.0.1:8000")

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down.")
```

### 3.2. Dependency Management

All required Python packages are listed in `requirements.txt`. The build process must ensure these dependencies are installed before running `PyInstaller`.

### 3.3. Static Assets

The `PyInstaller` specification file (`.spec`) will be configured to include all static assets from the `web/static/` directory. This ensures that the executable can serve all necessary HTML, CSS, and JavaScript files.

**Example `.spec` file configuration:**

```python
# In the .spec file

a = Analysis(['server_runner.py'],
             pathex=['/path/to/project'],
             binaries=[],
             datas=[('web/static', 'web/static'), ('web/templates', 'web/templates')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
```

## 4. Build & Distribution Workflow

### 4.1. Automation with GitHub Actions

A GitHub Actions workflow will be created to automate the build, packaging, and release process. The workflow configuration will be stored in `.github/workflows/release.yml`.

### 4.2. Build Trigger

The workflow will be triggered automatically when a new tag matching the pattern `v*.*.*` (e.g., `v1.0.0`) is pushed to the `main` branch.

### 4.3. Cross-Platform Builds

The workflow will consist of two parallel jobs:
- `build-macos`: Runs on `macos-latest`.
- `build-windows`: Runs on `windows-latest`.

Each job will perform the following steps:
1.  Check out the repository.
2.  Set up Python 3.11.
3.  Install dependencies from `requirements.txt`.
4.  Run `PyInstaller` to build the executable for the respective OS.
5.  Archive the executable and upload it as a workflow artifact.

### 4.4. Distribution

A final job, `create-release`, will run after both build jobs have succeeded.

**Responsibilities:**

1.  **Create GitHub Release:** It will create a new GitHub Release associated with the git tag that triggered the workflow.
2.  **Upload Assets:** It will download the build artifacts (macOS and Windows executables) and upload them as assets to the GitHub Release.

**Example GitHub Actions Workflow (`.github/workflows/release.yml`):**

```yaml
name: Create Release

on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build with PyInstaller
        run: pyinstaller --name "WorkJournalApp" --onefile --windowed --add-data "web/static:web/static" --add-data "web/templates:web/templates" server_runner.py
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: macos-build
          path: dist/WorkJournalApp

  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pyinstaller
      - name: Build with PyInstaller
        run: pyinstaller --name "WorkJournalApp" --onefile --windowed --add-data "web/static;web/static" --add-data "web/templates;web/templates" server_runner.py
      - name: Upload artifact
        uses: actions/upload-artifact@v3
        with:
          name: windows-build
          path: dist/WorkJournalApp.exe

  create-release:
    needs: [build-macos, build-windows]
    runs-on: ubuntu-latest
    steps:
      - name: Download macOS build
        uses: actions/download-artifact@v3
        with:
          name: macos-build
      - name: Download Windows build
        uses: actions/download-artifact@v3
        with:
          name: windows-build
      - name: Create Release
        id: create_release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
      - name: Upload macOS Release Asset
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./WorkJournalApp
          asset_name: WorkJournalApp-macOS
          asset_content_type: application/octet-stream
      - name: Upload Windows Release Asset
        uses: actions/upload-release-asset@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          upload_url: ${{ steps.create_release.outputs.upload_url }}
          asset_path: ./WorkJournalApp.exe
          asset_name: WorkJournalApp-Windows.exe
          asset_content_type: application/vnd.microsoft.portable-executable