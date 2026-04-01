# WorkJournalMaker Platform Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Transform WorkJournalMaker into a distributable, local-first, multi-user journaling platform with native installers (macOS/Windows), remote sync, and self-hostable server deployment.

**Architecture:** Five parallel tracks. Track A (local installer) is fully independent and can proceed immediately. Track B (multi-user foundation) is sequential and required before Tracks C (auth) and D (sync), which are parallel with each other. Track E (Docker) depends on C and D.

**Tech Stack:** PyInstaller, create-dmg, Inno Setup, GitHub Actions, SQLAlchemy, FastAPI, Google OAuth2, httpx

**Specs:**
- Installer: `docs/superpowers/specs/2026-03-31-local-installer-design.md`
- Sync: `implementation_plans/local_first_sync_plan.md`

---

## Dependency Graph

```
Track A: Local Installer (INDEPENDENT — start immediately)
  A1 ── A3 ──┐
  A2 ─────────┼── A4 ──┬── A5 ──┐
              │        └── A6 ──┼── A7
                                 │
Track B: Multi-User Foundation   │
  B1 ── B2 ── B3 ──┬── Track C  │
                    │            │
                    └── Track D  │
                                 │
Track C: Authentication          │
  C1 ────────────────┐           │
                     ├── E1      │
Track D: Sync Protocol│          │
  D1 ── D2 ──────────┘           │
                                 │
Track E: Docker                  │
  E1 ────────────────────────────┘
```

**Maximum parallelism at each stage:**

| Stage | Parallel subagents | Tasks |
|---|---|---|
| 1 | 3 | A1, A2, B1 |
| 2 | 2 | A3, B2 |
| 3 | 3 | A4, B3 |
| 4 | 3 | A5, A6, C1 |
| 5 | 3 | A7, D1 |
| 6 | 2 | D2, E1 |

---

## Track A: Local Installer

> **Independent of all other tracks.** Can start immediately and proceed without waiting for sync/auth work.

### Task A1: Rewrite PyInstaller Spec File

**Files:**
- Modify: `WorkJournalMaker.spec`
- Test: manual build verification in Task A5

- [ ] **Step 1: Rewrite the spec file**

Replace the entire contents of `WorkJournalMaker.spec`:

```python
# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec for WorkJournalMaker desktop application
# Entry point: server_runner.py (launches local web server + browser)

import sys
import os
from pathlib import Path

block_cipher = None
project_root = os.path.abspath('.')

# Collect all data files
datas = [
    ('web/static', 'web/static'),
    ('web/templates', 'web/templates'),
]

# Include config files if present
for config_name in ['config.yaml', 'config.json', 'settings.yaml']:
    if os.path.exists(os.path.join(project_root, config_name)):
        datas.append((config_name, '.'))

a = Analysis(
    ['server_runner.py'],
    pathex=[project_root],
    binaries=[],
    datas=datas,
    hiddenimports=[
        # Application modules
        'desktop.desktop_app',
        'desktop.server_manager',
        'desktop.browser_controller',
        'desktop.platform_compat',
        'desktop.port_detector',
        'desktop.readiness_checker',
        'desktop.runtime_detector',
        'desktop.app_logger',
        'web.app',
        'web.database',
        'web.middleware',
        'web.api.health',
        'web.api.entries',
        'web.api.sync',
        'web.api.calendar',
        'web.api.summarization',
        'web.api.settings',
        'web.services.entry_manager',
        'web.services.calendar_service',
        'web.services.settings_service',
        'web.services.web_summarizer',
        'web.services.work_week_service',
        'web.services.base_service',
        'config_manager',
        'file_discovery',
        'content_processor',
        'unified_llm_client',
        'logger',
        # Uvicorn
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        # FastAPI/Starlette
        'fastapi.routing',
        'fastapi.responses',
        'fastapi.encoders',
        'fastapi.exceptions',
        'starlette.routing',
        'starlette.responses',
        'starlette.middleware',
        'starlette.staticfiles',
        # Database
        'sqlalchemy.ext.declarative',
        'sqlalchemy.sql.default_comparator',
        'aiosqlite',
        # Templates
        'jinja2.ext',
        # Standard library
        'asyncio',
        'concurrent.futures',
        'multiprocessing',
        'queue',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter',
        'matplotlib', 'matplotlib.pyplot',
        'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
        'pytest', 'pytest_cov', 'pytest_mock', 'coverage',
        'black', 'flake8', 'mypy',
        'sphinx', 'docutils',
        'jupyter', 'notebook', 'ipython', 'IPython',
        'pandas', 'numpy', 'scipy', 'sklearn',
        'tensorflow', 'torch', 'cv2',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WorkJournalMaker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # --windowed: no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.icns' if sys.platform == 'darwin' else 'assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='WorkJournalMaker',
)

# macOS .app bundle
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='WorkJournalMaker.app',
        icon='assets/icon.icns',
        bundle_identifier='com.workjournalmaker.app',
        info_plist={
            'CFBundleDisplayName': 'Work Journal Maker',
            'CFBundleShortVersionString': '1.0.0',
            'CFBundleVersion': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.15',
        },
    )
```

- [ ] **Step 2: Commit**

```bash
git add WorkJournalMaker.spec
git commit -m "feat: rewrite spec for desktop app with server_runner entry point"
```

---

### Task A2: Create App Icons

**Files:**
- Create: `assets/icon.icns` (macOS)
- Create: `assets/icon.ico` (Windows)
- Create: `assets/icon_source.png` (1024x1024 source image)

- [ ] **Step 1: Create assets directory and placeholder icons**

Generate a simple placeholder icon programmatically. We need a 1024x1024 PNG, then convert to `.icns` and `.ico`.

```bash
mkdir -p assets
```

Create a Python script to generate the placeholder icon:

```python
# scripts/generate_icons.py
"""Generate placeholder app icons for macOS and Windows."""
import struct
import zlib
import os

def create_png(width, height, color_rgb, text_color_rgb, output_path):
    """Create a simple colored PNG with 'WJ' text-like pattern."""
    # Create raw pixel data - simple solid color with a border
    pixels = []
    border = width // 10
    for y in range(height):
        row = []
        for x in range(width):
            if x < border or x >= width - border or y < border or y >= height - border:
                row.extend(text_color_rgb)
                row.append(255)
            else:
                row.extend(color_rgb)
                row.append(255)
        pixels.append(bytes([0] + row))  # filter byte + RGBA

    raw = b''.join(pixels)

    def chunk(chunk_type, data):
        c = chunk_type + data
        crc = struct.pack('>I', zlib.crc32(c) & 0xffffffff)
        return struct.pack('>I', len(data)) + c + crc

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0)
    idat = zlib.compress(raw, 9)

    with open(output_path, 'wb') as f:
        f.write(header)
        f.write(chunk(b'IHDR', ihdr))
        f.write(chunk(b'IDAT', idat))
        f.write(chunk(b'IEND', b''))

def create_ico(png_path, ico_path):
    """Create a minimal .ico from a PNG file."""
    with open(png_path, 'rb') as f:
        png_data = f.read()

    # ICO header: reserved(2) + type(2) + count(2)
    header = struct.pack('<HHH', 0, 1, 1)
    # Directory entry: w, h, colors, reserved, planes, bpp, size, offset
    entry = struct.pack('<BBBBHHIH', 0, 0, 0, 0, 1, 32, len(png_data), 22)

    with open(ico_path, 'wb') as f:
        f.write(header + entry + png_data)

if __name__ == '__main__':
    # Blue background with white border
    blue = [41, 98, 255]
    white = [255, 255, 255]

    os.makedirs('assets', exist_ok=True)

    # Generate source PNG at multiple sizes
    create_png(1024, 1024, blue, white, 'assets/icon_source.png')
    create_png(256, 256, blue, white, 'assets/icon_256.png')

    # Create .ico for Windows
    create_ico('assets/icon_256.png', 'assets/icon.ico')

    print("Generated: assets/icon_source.png, assets/icon_256.png, assets/icon.ico")
    print("NOTE: For macOS .icns, run on macOS:")
    print("  mkdir icon.iconset")
    print("  sips -z 1024 1024 assets/icon_source.png --out icon.iconset/icon_512x512@2x.png")
    print("  sips -z 512 512 assets/icon_source.png --out icon.iconset/icon_512x512.png")
    print("  sips -z 256 256 assets/icon_source.png --out icon.iconset/icon_256x256.png")
    print("  sips -z 128 128 assets/icon_source.png --out icon.iconset/icon_128x128.png")
    print("  sips -z 64 64 assets/icon_source.png --out icon.iconset/icon_64x64.png")
    print("  sips -z 32 32 assets/icon_source.png --out icon.iconset/icon_32x32.png")
    print("  sips -z 16 16 assets/icon_source.png --out icon.iconset/icon_16x16.png")
    print("  iconutil -c icns icon.iconset -o assets/icon.icns")
    print("  rm -rf icon.iconset")
```

- [ ] **Step 2: Run icon generation**

```bash
python scripts/generate_icons.py
```

- [ ] **Step 3: Generate macOS .icns (on macOS only)**

```bash
mkdir -p icon.iconset
sips -z 1024 1024 assets/icon_source.png --out icon.iconset/icon_512x512@2x.png
sips -z 512 512 assets/icon_source.png --out icon.iconset/icon_512x512.png
sips -z 256 256 assets/icon_source.png --out icon.iconset/icon_256x256.png
sips -z 128 128 assets/icon_source.png --out icon.iconset/icon_128x128.png
sips -z 64 64 assets/icon_source.png --out icon.iconset/icon_64x64.png
sips -z 32 32 assets/icon_source.png --out icon.iconset/icon_32x32.png
sips -z 16 16 assets/icon_source.png --out icon.iconset/icon_16x16.png
iconutil -c icns icon.iconset -o assets/icon.icns
rm -rf icon.iconset
```

- [ ] **Step 4: Commit**

```bash
git add assets/ scripts/generate_icons.py
git commit -m "feat: add placeholder app icons for macOS and Windows"
```

---

### Task A3: Simplify Build System

**Files:**
- Modify: `build_system/build_config.py` — remove `PyInstallerSpecGenerator`, keep `BuildConfig`
- Modify: `build_system/local_builder.py` — simplify to thin wrapper
- Modify: `scripts/build.py` — simplify CLI
- Modify: `tests/test_build_config.py` — remove spec generator tests
- Modify: `tests/test_local_build.py` — update for simplified builder

- [ ] **Step 1: Write failing test for simplified builder**

Create a test for the simplified builder interface:

```python
# In tests/test_local_build.py — replace or update existing tests
def test_simplified_builder_init(tmp_path):
    """Builder initializes with project root and finds spec file."""
    # Create minimal project structure
    spec_file = tmp_path / "WorkJournalMaker.spec"
    spec_file.write_text("# -*- mode: python ; coding: utf-8 -*-\na = Analysis(['server_runner.py'])\npyz = PYZ(a.pure)\nexe = EXE(pyz, a.scripts)")
    entry_point = tmp_path / "server_runner.py"
    entry_point.write_text("# entry point")

    builder = LocalBuilder(project_root=str(tmp_path))
    assert builder.project_root == tmp_path
    assert builder.spec_file == spec_file


def test_simplified_builder_generates_command(tmp_path):
    """Builder generates correct pyinstaller command."""
    spec_file = tmp_path / "WorkJournalMaker.spec"
    spec_file.write_text("# -*- mode: python ; coding: utf-8 -*-\na = Analysis(['server_runner.py'])\npyz = PYZ(a.pure)\nexe = EXE(pyz, a.scripts)")
    entry_point = tmp_path / "server_runner.py"
    entry_point.write_text("# entry point")

    builder = LocalBuilder(project_root=str(tmp_path))
    cmd = builder.generate_build_command(clean=True)

    assert cmd[0] == 'pyinstaller'
    assert str(spec_file) in cmd
    assert '--clean' in cmd
```

- [ ] **Step 2: Run tests to verify they pass with existing code**

```bash
pytest tests/test_local_build.py::test_simplified_builder_init tests/test_local_build.py::test_simplified_builder_generates_command -v
```

The existing `LocalBuilder` should pass these since the interface is compatible.

- [ ] **Step 3: Remove PyInstallerSpecGenerator from build_config.py**

Remove the `PyInstallerSpecGenerator` class and the `generate_spec_file()` convenience function from `build_system/build_config.py`. Keep `BuildConfig` and `create_build_config()`.

- [ ] **Step 4: Update tests to remove spec generator tests**

Remove test classes `TestPyInstallerSpecGenerator` from `tests/test_build_config.py`.

- [ ] **Step 5: Run all build tests**

```bash
pytest tests/test_build_config.py tests/test_local_build.py -v
```

Expected: all remaining tests pass.

- [ ] **Step 6: Commit**

```bash
git add build_system/ tests/test_build_config.py tests/test_local_build.py
git commit -m "refactor: simplify build system, remove spec generator"
```

---

### Task A4: Verify Working Local Build (macOS)

**Files:**
- No new files — this validates that Tasks A1-A3 produce a working executable

**Prerequisites:** Tasks A1, A2, A3 must be complete.

- [ ] **Step 1: Run PyInstaller build**

```bash
pyenv activate WorkJournal
pyinstaller WorkJournalMaker.spec --clean
```

Expected: build completes without errors, output in `dist/WorkJournalMaker/` (onedir) or `dist/WorkJournalMaker.app/` (macOS).

- [ ] **Step 2: Verify executable exists**

```bash
ls -la dist/WorkJournalMaker.app/Contents/MacOS/WorkJournalMaker  # macOS
# OR
ls -la dist/WorkJournalMaker/WorkJournalMaker  # Linux/generic
```

- [ ] **Step 3: Test executable launches**

```bash
# Run with --help to verify it starts without crashing
dist/WorkJournalMaker.app/Contents/MacOS/WorkJournalMaker --help
```

Expected: prints help text from `server_runner.py`'s argparse.

- [ ] **Step 4: Test full launch (manual)**

```bash
# Launch the app — it should start uvicorn and open browser
dist/WorkJournalMaker.app/Contents/MacOS/WorkJournalMaker --no-browser
# Wait 5 seconds, then Ctrl+C
```

Expected: server starts on a port, prints URL, shuts down cleanly.

- [ ] **Step 5: Document any issues found and fix**

If hidden imports are missing or data files aren't bundled correctly, update `WorkJournalMaker.spec` and rebuild.

- [ ] **Step 6: Commit any spec fixes**

```bash
git add WorkJournalMaker.spec
git commit -m "fix: resolve pyinstaller bundling issues found during testing"
```

---

### Task A5: macOS Installer Script

**Files:**
- Create: `installer/macos/create-dmg.sh`
- Test: manual DMG creation

**Prerequisites:** Task A4 (working build).

- [ ] **Step 1: Install create-dmg**

```bash
brew install create-dmg
```

- [ ] **Step 2: Create the installer script**

```bash
#!/bin/bash
# ABOUTME: Creates a macOS .dmg installer from the PyInstaller .app bundle
# ABOUTME: Wraps create-dmg with project-specific settings

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
APP_NAME="WorkJournalMaker"
APP_PATH="$PROJECT_ROOT/dist/${APP_NAME}.app"
DMG_OUTPUT="$PROJECT_ROOT/dist/${APP_NAME}.dmg"
VOLUME_NAME="Work Journal Maker"

# Verify .app exists
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: $APP_PATH not found. Run PyInstaller build first."
    exit 1
fi

# Remove old DMG if it exists
rm -f "$DMG_OUTPUT"

echo "Creating DMG installer..."

create-dmg \
    --volname "$VOLUME_NAME" \
    --window-pos 200 120 \
    --window-size 600 400 \
    --icon-size 100 \
    --icon "$APP_NAME.app" 150 190 \
    --app-drop-link 450 190 \
    --no-internet-enable \
    "$DMG_OUTPUT" \
    "$APP_PATH"

echo "DMG created: $DMG_OUTPUT"
echo "Size: $(du -h "$DMG_OUTPUT" | cut -f1)"
```

- [ ] **Step 3: Make executable and test**

```bash
chmod +x installer/macos/create-dmg.sh
./installer/macos/create-dmg.sh
```

Expected: `dist/WorkJournalMaker.dmg` is created.

- [ ] **Step 4: Verify DMG manually**

```bash
open dist/WorkJournalMaker.dmg
```

Expected: a Finder window opens showing the app icon and an Applications shortcut.

- [ ] **Step 5: Commit**

```bash
git add installer/macos/create-dmg.sh
git commit -m "feat: add macOS DMG installer script"
```

---

### Task A6: Windows Installer Config

**Files:**
- Create: `installer/windows/installer.iss`

- [ ] **Step 1: Create Inno Setup script**

```iss
; ABOUTME: Inno Setup script for WorkJournalMaker Windows installer
; ABOUTME: Creates a standard Windows setup wizard with Start Menu and Desktop shortcuts

#define MyAppName "Work Journal Maker"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "WorkJournalMaker"
#define MyAppURL "https://github.com/lbnl-science-it/WorkJournalMaker"
#define MyAppExeName "WorkJournalMaker.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=..\..\dist
OutputBaseFilename=WorkJournalMaker-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "..\..\dist\WorkJournalMaker\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#MyAppName}}"; Flags: nowait postinstall skipifsilent
```

- [ ] **Step 2: Commit**

```bash
git add installer/windows/installer.iss
git commit -m "feat: add Windows Inno Setup installer configuration"
```

---

### Task A7: CI/CD Release Workflow

**Files:**
- Modify: `.github/workflows/release.yml` — rewrite for proper installer creation

**Prerequisites:** Tasks A5, A6 (installer configs exist).

- [ ] **Step 1: Rewrite release.yml**

```yaml
# ABOUTME: CI/CD workflow for building macOS and Windows installers
# ABOUTME: Triggered by version tags, creates GitHub Release with installer artifacts

name: Build and Release Desktop Installers

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:
    inputs:
      create_release:
        description: 'Create a GitHub Release'
        required: false
        default: 'false'

permissions:
  contents: write

jobs:
  test:
    name: Run Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v --tb=short -x

  build-macos:
    name: Build macOS Installer
    needs: test
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller
          brew install create-dmg

      - name: Build with PyInstaller
        run: pyinstaller WorkJournalMaker.spec --clean

      - name: Verify .app bundle
        run: |
          test -d dist/WorkJournalMaker.app
          test -f dist/WorkJournalMaker.app/Contents/MacOS/WorkJournalMaker

      - name: Create DMG
        run: ./installer/macos/create-dmg.sh

      - name: Upload DMG
        uses: actions/upload-artifact@v4
        with:
          name: WorkJournalMaker-macOS
          path: dist/WorkJournalMaker.dmg

  build-windows:
    name: Build Windows Installer
    needs: test
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pyinstaller

      - name: Build with PyInstaller
        run: pyinstaller WorkJournalMaker.spec --clean

      - name: Verify executable
        run: |
          Test-Path dist\WorkJournalMaker\WorkJournalMaker.exe
        shell: pwsh

      - name: Install Inno Setup
        run: choco install innosetup -y

      - name: Build installer
        run: iscc installer\windows\installer.iss

      - name: Upload Setup.exe
        uses: actions/upload-artifact@v4
        with:
          name: WorkJournalMaker-Windows
          path: dist/WorkJournalMaker-Setup.exe

  release:
    name: Create GitHub Release
    needs: [build-macos, build-windows]
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v') || github.event.inputs.create_release == 'true'
    steps:
      - name: Download macOS artifact
        uses: actions/download-artifact@v4
        with:
          name: WorkJournalMaker-macOS
          path: release/

      - name: Download Windows artifact
        uses: actions/download-artifact@v4
        with:
          name: WorkJournalMaker-Windows
          path: release/

      - name: Create Release
        uses: softprops/action-gh-release@v2
        with:
          files: |
            release/WorkJournalMaker.dmg
            release/WorkJournalMaker-Setup.exe
          generate_release_notes: true
          draft: false
          prerelease: false
```

- [ ] **Step 2: Run workflow validation**

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/release.yml'))"
```

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/release.yml
git commit -m "feat: rewrite release workflow for macOS/Windows installers"
```

---

## Track B: Multi-User Foundation

> **Sequential track.** B1 → B2 → B3. Can run in parallel with Track A.

### Task B1: Multi-User Database Schema

**Files:**
- Modify: `web/database.py` — add `User` model, add `user_id` to `JournalEntryIndex`
- Create: `tests/test_multi_user_schema.py`

- [ ] **Step 1: Write failing test for User model**

```python
# tests/test_multi_user_schema.py
"""Tests for multi-user database schema."""
import pytest
from datetime import datetime, date
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session
from web.database import Base, User, JournalEntryIndex


@pytest.fixture
def engine():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture
def session(engine):
    with Session(engine) as session:
        yield session


class TestUserModel:
    def test_create_user(self, session):
        """User model can be created and persisted."""
        user = User(
            id="user-123",
            email="test@lbl.gov",
            display_name="Test User",
            storage_path="/data/users/user-123/worklogs",
        )
        session.add(user)
        session.commit()

        result = session.query(User).filter_by(id="user-123").first()
        assert result is not None
        assert result.email == "test@lbl.gov"
        assert result.display_name == "Test User"

    def test_user_email_unique(self, session):
        """Email must be unique across users."""
        user1 = User(id="u1", email="same@lbl.gov", display_name="User 1")
        user2 = User(id="u2", email="same@lbl.gov", display_name="User 2")
        session.add(user1)
        session.commit()
        session.add(user2)
        with pytest.raises(Exception):  # IntegrityError
            session.commit()

    def test_local_user_default(self, session):
        """A 'local' user exists for single-user mode."""
        user = User(id="local", display_name="Local User")
        session.add(user)
        session.commit()
        result = session.query(User).filter_by(id="local").first()
        assert result is not None


class TestJournalEntryUserScope:
    def test_entry_has_user_id(self, session):
        """JournalEntryIndex has a user_id column."""
        entry = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/worklogs/worklog_2024-01-15.txt",
            user_id="local",
            has_content=True,
        )
        session.add(entry)
        session.commit()

        result = session.query(JournalEntryIndex).first()
        assert result.user_id == "local"

    def test_same_date_different_users(self, session):
        """Two users can have entries for the same date."""
        entry1 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/user1/worklog.txt",
            user_id="user-1",
            has_content=True,
        )
        entry2 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/user2/worklog.txt",
            user_id="user-2",
            has_content=True,
        )
        session.add_all([entry1, entry2])
        session.commit()

        results = session.query(JournalEntryIndex).filter_by(
            date=date(2024, 1, 15)
        ).all()
        assert len(results) == 2

    def test_same_date_same_user_rejected(self, session):
        """Same user cannot have two entries for the same date."""
        entry1 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/path1.txt",
            user_id="local",
            has_content=True,
        )
        entry2 = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/path2.txt",
            user_id="local",
            has_content=True,
        )
        session.add(entry1)
        session.commit()
        session.add(entry2)
        with pytest.raises(Exception):  # IntegrityError
            session.commit()

    def test_default_user_id_is_local(self, session):
        """Entries without explicit user_id default to 'local'."""
        entry = JournalEntryIndex(
            date=date(2024, 1, 15),
            file_path="/worklogs/worklog.txt",
            has_content=True,
        )
        session.add(entry)
        session.commit()

        result = session.query(JournalEntryIndex).first()
        assert result.user_id == "local"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_multi_user_schema.py -v
```

Expected: FAIL — `User` class doesn't exist, `user_id` column missing from `JournalEntryIndex`.

- [ ] **Step 3: Add User model to web/database.py**

Add after existing model definitions:

```python
class User(Base):
    """User account for multi-user support."""
    __tablename__ = "users"

    id = Column(String, primary_key=True)  # UUID or "local"
    email = Column(String, unique=True, nullable=True)
    display_name = Column(String, nullable=True)
    storage_path = Column(String, nullable=True)  # per-user file root
    created_at = Column(DateTime, default=now_utc)
    last_sync_at = Column(DateTime, nullable=True)
```

- [ ] **Step 4: Add user_id to JournalEntryIndex**

Modify the existing `JournalEntryIndex` class:

```python
# Add column:
user_id = Column(String, default="local", nullable=False, index=True)

# Change unique constraint from:
#   UniqueConstraint('date')
# To:
__table_args__ = (
    UniqueConstraint('user_id', 'date', name='uq_user_date'),
    Index('idx_journal_entries_date_content', 'date', 'has_content'),
    Index('idx_journal_entries_week_ending', 'week_ending_date'),
    Index('idx_journal_entries_user', 'user_id'),
)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
pytest tests/test_multi_user_schema.py -v
```

Expected: all PASS.

- [ ] **Step 6: Run existing tests to verify no regressions**

```bash
pytest tests/ -v --tb=short -x -k "not test_local_build and not test_build_config"
```

Expected: existing tests pass. Some may need `user_id="local"` added if they create JournalEntryIndex directly.

- [ ] **Step 7: Fix any broken existing tests**

Add `user_id="local"` to any test fixtures that create `JournalEntryIndex` without it.

- [ ] **Step 8: Commit**

```bash
git add web/database.py tests/test_multi_user_schema.py tests/
git commit -m "feat: add User model and user_id scoping to journal entries"
```

---

### Task B2: User-Scoped Services

**Files:**
- Modify: `web/services/entry_manager.py` — accept `user_id` parameter
- Modify: `web/services/calendar_service.py` — accept `user_id` parameter
- Modify: `web/services/web_summarizer.py` — accept `user_id` parameter
- Modify: `web/services/settings_service.py` — accept `user_id` parameter
- Create: `tests/test_user_scoped_services.py`

- [ ] **Step 1: Write failing test for user-scoped EntryManager**

```python
# tests/test_user_scoped_services.py
"""Tests for user-scoped service methods."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date


class TestEntryManagerUserScope:
    @pytest.mark.asyncio
    async def test_get_entry_scoped_to_user(self):
        """EntryManager.get_entry_by_date accepts user_id parameter."""
        from web.services.entry_manager import EntryManager

        manager = EntryManager.__new__(EntryManager)
        manager.config = MagicMock()
        manager.logger = MagicMock()
        manager.db_manager = MagicMock()
        manager._work_week_service = None

        # Verify the method signature accepts user_id
        import inspect
        sig = inspect.signature(manager.get_entry_by_date)
        assert 'user_id' in sig.parameters

    @pytest.mark.asyncio
    async def test_default_user_id_is_local(self):
        """When user_id is not provided, it defaults to 'local'."""
        from web.services.entry_manager import EntryManager

        import inspect
        sig = inspect.signature(EntryManager.get_entry_by_date)
        user_id_param = sig.parameters.get('user_id')
        assert user_id_param is not None
        assert user_id_param.default == "local"


class TestCalendarServiceUserScope:
    def test_get_calendar_month_accepts_user_id(self):
        """CalendarService.get_calendar_month accepts user_id parameter."""
        from web.services.calendar_service import CalendarService

        import inspect
        sig = inspect.signature(CalendarService.get_calendar_month)
        assert 'user_id' in sig.parameters


class TestSettingsServiceUserScope:
    def test_get_all_settings_accepts_user_id(self):
        """SettingsService.get_all_settings accepts user_id parameter."""
        from web.services.settings_service import SettingsService

        import inspect
        sig = inspect.signature(SettingsService.get_all_settings)
        assert 'user_id' in sig.parameters
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_user_scoped_services.py -v
```

Expected: FAIL — methods don't have `user_id` parameter yet.

- [ ] **Step 3: Add user_id parameter to EntryManager methods**

Add `user_id: str = "local"` parameter to these methods in `web/services/entry_manager.py`:
- `get_entry_content(self, entry_date, user_id="local")`
- `save_entry_content(self, entry_date, content, user_id="local")`
- `get_entry_by_date(self, entry_date, include_content=False, user_id="local")`
- `get_recent_entries(self, limit=10, user_id="local")`
- `list_entries(self, request, user_id="local")`
- `delete_entry(self, entry_date, user_id="local")`

In each method, pass `user_id` to database queries by adding `.filter_by(user_id=user_id)` to existing query chains. For file path construction, use the user's storage path when `user_id != "local"`.

- [ ] **Step 4: Add user_id parameter to CalendarService methods**

Add `user_id: str = "local"` to:
- `get_calendar_month(self, year, month, user_id="local")`
- `get_entries_for_date_range(self, start_date, end_date, user_id="local")`
- `has_entry_for_date(self, entry_date, user_id="local")`

- [ ] **Step 5: Add user_id parameter to SettingsService methods**

Add `user_id: str = "local"` to:
- `get_all_settings(self, user_id="local")`
- `get_setting(self, key, user_id="local")`
- `update_setting(self, key, value, user_id="local")`

- [ ] **Step 6: Add user_id parameter to WebSummarizationService**

Add `user_id: str = "local"` to the summarize method.

- [ ] **Step 7: Run tests**

```bash
pytest tests/test_user_scoped_services.py -v
```

Expected: PASS.

- [ ] **Step 8: Run full test suite for regressions**

```bash
pytest tests/ -v --tb=short -x -k "not test_local_build and not test_build_config"
```

Expected: all pass — default `user_id="local"` preserves existing behavior.

- [ ] **Step 9: Commit**

```bash
git add web/services/ tests/test_user_scoped_services.py
git commit -m "feat: thread user_id through all services with 'local' default"
```

---

### Task B3: Server Mode Configuration

**Files:**
- Modify: `config_manager.py` — add `ServerConfig`, `AuthConfig`, `SyncConfig` dataclasses
- Create: `tests/test_server_config.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_server_config.py
"""Tests for server mode configuration."""
import pytest
from config_manager import ServerConfig, AuthConfig, SyncConfig, AppConfig


class TestServerConfig:
    def test_default_mode_is_local(self):
        config = ServerConfig()
        assert config.mode == "local"

    def test_server_mode_requires_storage_root(self):
        config = ServerConfig(mode="server", storage_root="/data/users/")
        assert config.storage_root == "/data/users/"

    def test_local_mode_ignores_storage_root(self):
        config = ServerConfig(mode="local")
        assert config.storage_root is None


class TestAuthConfig:
    def test_auth_disabled_by_default(self):
        config = AuthConfig()
        assert config.enabled is False

    def test_google_auth_config(self):
        config = AuthConfig(
            enabled=True,
            provider="google",
            google_client_id="test-client-id",
            allowed_domains=["lbl.gov"],
        )
        assert config.provider == "google"
        assert "lbl.gov" in config.allowed_domains


class TestSyncConfig:
    def test_sync_disabled_by_default(self):
        config = SyncConfig()
        assert config.enabled is False

    def test_sync_with_remote_url(self):
        config = SyncConfig(
            enabled=True,
            remote_url="https://journal.example.com",
            auth_token="test-token",
        )
        assert config.remote_url == "https://journal.example.com"

    def test_auto_sync_interval_default(self):
        config = SyncConfig()
        assert config.auto_sync_interval == 0  # manual only


class TestAppConfigIntegration:
    def test_app_config_includes_server_config(self):
        config = AppConfig()
        assert hasattr(config, 'server')
        assert isinstance(config.server, ServerConfig)

    def test_app_config_includes_auth_config(self):
        config = AppConfig()
        assert hasattr(config, 'auth')
        assert isinstance(config.auth, AuthConfig)

    def test_app_config_includes_sync_config(self):
        config = AppConfig()
        assert hasattr(config, 'sync')
        assert isinstance(config.sync, SyncConfig)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_server_config.py -v
```

Expected: FAIL — `ServerConfig`, `AuthConfig`, `SyncConfig` don't exist.

- [ ] **Step 3: Add dataclasses to config_manager.py**

```python
@dataclass
class ServerConfig:
    """Server mode configuration."""
    mode: str = "local"  # "local" or "server"
    storage_root: Optional[str] = None  # per-user file root in server mode

@dataclass
class AuthConfig:
    """Authentication configuration for server mode."""
    enabled: bool = False
    provider: str = "google"  # "google" or "api_key"
    google_client_id: str = ""
    google_client_secret: str = ""
    allowed_domains: list = field(default_factory=list)

@dataclass
class SyncConfig:
    """Sync client configuration for local mode."""
    enabled: bool = False
    remote_url: str = ""
    auth_token: str = ""
    auto_sync_interval: int = 0  # seconds, 0 = manual only

@dataclass
class AppConfig:
    # ... existing fields ...
    server: ServerConfig = field(default_factory=ServerConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    sync: SyncConfig = field(default_factory=SyncConfig)
```

- [ ] **Step 4: Add YAML parsing for new config sections**

In `ConfigManager._parse_config_dict()`, add parsing for `server:`, `auth:`, and `sync:` sections.

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_server_config.py -v
```

Expected: PASS.

- [ ] **Step 6: Run full test suite**

```bash
pytest tests/ -v --tb=short -x -k "not test_local_build and not test_build_config"
```

- [ ] **Step 7: Commit**

```bash
git add config_manager.py tests/test_server_config.py
git commit -m "feat: add server, auth, and sync configuration dataclasses"
```

---

## Track C: Authentication

> **Depends on Track B completion (B3 specifically).** Can run in parallel with Track D.

### Task C1: Authentication Service and Middleware

**Files:**
- Create: `web/services/auth_service.py`
- Modify: `web/middleware.py` — add auth middleware
- Modify: `web/app.py` — conditionally enable auth
- Create: `tests/test_auth_service.py`

- [ ] **Step 1: Write failing tests for auth service**

```python
# tests/test_auth_service.py
"""Tests for authentication service."""
import pytest
from web.services.auth_service import AuthService, AuthResult


class TestAPIKeyAuth:
    def test_valid_api_key(self):
        """Valid API key returns authenticated result."""
        service = AuthService(
            enabled=True,
            provider="api_key",
            api_keys={"test-key-123": "user-1"},
        )
        result = service.authenticate_api_key("test-key-123")
        assert result.authenticated is True
        assert result.user_id == "user-1"

    def test_invalid_api_key(self):
        """Invalid API key returns unauthenticated result."""
        service = AuthService(
            enabled=True,
            provider="api_key",
            api_keys={"test-key-123": "user-1"},
        )
        result = service.authenticate_api_key("wrong-key")
        assert result.authenticated is False

    def test_auth_disabled_returns_local(self):
        """When auth is disabled, all requests are user 'local'."""
        service = AuthService(enabled=False)
        result = service.authenticate_api_key("anything")
        assert result.authenticated is True
        assert result.user_id == "local"


class TestAuthResult:
    def test_auth_result_fields(self):
        result = AuthResult(authenticated=True, user_id="user-1")
        assert result.authenticated is True
        assert result.user_id == "user-1"
        assert result.error is None

    def test_auth_result_with_error(self):
        result = AuthResult(authenticated=False, error="Invalid token")
        assert result.authenticated is False
        assert result.user_id is None
        assert result.error == "Invalid token"
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_auth_service.py -v
```

- [ ] **Step 3: Implement auth service**

```python
# web/services/auth_service.py
# ABOUTME: Authentication service supporting API key and Google OAuth2
# ABOUTME: Disabled in local mode, returns user_id="local" for all requests

from dataclasses import dataclass
from typing import Optional, Dict


@dataclass
class AuthResult:
    """Result of an authentication attempt."""
    authenticated: bool
    user_id: Optional[str] = None
    error: Optional[str] = None


class AuthService:
    """Authentication service for multi-user server mode."""

    def __init__(
        self,
        enabled: bool = False,
        provider: str = "api_key",
        api_keys: Optional[Dict[str, str]] = None,
        google_client_id: str = "",
        allowed_domains: Optional[list] = None,
    ):
        self.enabled = enabled
        self.provider = provider
        self.api_keys = api_keys or {}
        self.google_client_id = google_client_id
        self.allowed_domains = allowed_domains or []

    def authenticate_api_key(self, key: str) -> AuthResult:
        """Authenticate using an API key."""
        if not self.enabled:
            return AuthResult(authenticated=True, user_id="local")

        user_id = self.api_keys.get(key)
        if user_id:
            return AuthResult(authenticated=True, user_id=user_id)
        return AuthResult(authenticated=False, error="Invalid API key")

    def authenticate_bearer_token(self, token: str) -> AuthResult:
        """Authenticate using a bearer token (Google OAuth2)."""
        if not self.enabled:
            return AuthResult(authenticated=True, user_id="local")

        # Google OAuth2 token verification — placeholder for real implementation
        # In production: verify token with Google, extract email, check allowed_domains
        return AuthResult(authenticated=False, error="OAuth2 not yet implemented")
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_auth_service.py -v
```

Expected: PASS.

- [ ] **Step 5: Add auth middleware to web/middleware.py**

```python
class AuthMiddleware(BaseHTTPMiddleware):
    """Authentication middleware — only active in server mode."""

    async def dispatch(self, request, call_next):
        auth_service = getattr(request.app.state, 'auth_service', None)

        if auth_service is None or not auth_service.enabled:
            request.state.user_id = "local"
            return await call_next(request)

        # Skip auth for health endpoints
        if request.url.path.startswith("/api/health"):
            request.state.user_id = "local"
            return await call_next(request)

        # Check API key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            result = auth_service.authenticate_api_key(api_key)
            if result.authenticated:
                request.state.user_id = result.user_id
                return await call_next(request)

        # Check Bearer token
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            result = auth_service.authenticate_bearer_token(token)
            if result.authenticated:
                request.state.user_id = result.user_id
                return await call_next(request)

        return JSONResponse(status_code=401, content={"detail": "Authentication required"})
```

- [ ] **Step 6: Conditionally enable auth in web/app.py**

In `WorkJournalWebApp`, after config loading:

```python
# In startup sequence, after config is loaded:
if self.config.auth.enabled:
    from web.services.auth_service import AuthService
    auth_service = AuthService(
        enabled=True,
        provider=self.config.auth.provider,
        google_client_id=self.config.auth.google_client_id,
        allowed_domains=self.config.auth.allowed_domains,
    )
    self.app.state.auth_service = auth_service
    # Add middleware
    from web.middleware import AuthMiddleware
    self.app.add_middleware(AuthMiddleware)
```

- [ ] **Step 7: Run full test suite**

```bash
pytest tests/ -v --tb=short -x -k "not test_local_build and not test_build_config"
```

- [ ] **Step 8: Commit**

```bash
git add web/services/auth_service.py web/middleware.py web/app.py tests/test_auth_service.py
git commit -m "feat: add auth service and middleware (disabled in local mode)"
```

---

## Track D: Sync Protocol

> **Depends on Track B completion (B3 specifically).** Can run in parallel with Track C.

### Task D1: Sync API Endpoints (Server Side)

**Files:**
- Create: `web/api/remote_sync.py` — sync router
- Create: `web/services/remote_sync_service.py` — sync logic
- Modify: `web/app.py` — include sync router
- Create: `tests/test_remote_sync.py`

- [ ] **Step 1: Write failing test for manifest generation**

```python
# tests/test_remote_sync.py
"""Tests for remote sync service and API."""
import pytest
from datetime import date, datetime
from web.services.remote_sync_service import RemoteSyncService, FileManifest, ManifestEntry


class TestManifestGeneration:
    def test_generate_manifest_from_files(self, tmp_path):
        """Generate manifest from a directory of journal files."""
        # Create sample files
        journal_dir = tmp_path / "worklogs"
        journal_dir.mkdir()
        file1 = journal_dir / "worklog_2024-01-15.txt"
        file1.write_text("Today I worked on X.")
        file2 = journal_dir / "worklog_2024-01-16.txt"
        file2.write_text("Today I worked on Y.")

        service = RemoteSyncService(storage_root=str(tmp_path))
        manifest = service.generate_manifest(user_id="local")

        assert len(manifest.entries) == 2
        assert all(isinstance(e, ManifestEntry) for e in manifest.entries)

    def test_manifest_entry_has_hash(self, tmp_path):
        """Each manifest entry includes a SHA256 hash."""
        journal_dir = tmp_path / "worklogs"
        journal_dir.mkdir()
        file1 = journal_dir / "worklog_2024-01-15.txt"
        file1.write_text("Today I worked on X.")

        service = RemoteSyncService(storage_root=str(tmp_path))
        manifest = service.generate_manifest(user_id="local")

        entry = manifest.entries[0]
        assert entry.sha256 is not None
        assert len(entry.sha256) == 64  # SHA256 hex digest length


class TestManifestComparison:
    def test_compare_identical_manifests(self):
        """Identical manifests produce no diff."""
        entries = [
            ManifestEntry(
                relative_path="worklog_2024-01-15.txt",
                sha256="abc123" * 10 + "abcd",
                modified_at=datetime(2024, 1, 15, 12, 0),
            )
        ]
        client_manifest = FileManifest(entries=entries)
        server_manifest = FileManifest(entries=entries)

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(client_manifest, server_manifest)

        assert len(diff.to_upload) == 0
        assert len(diff.to_download) == 0

    def test_client_has_new_file(self):
        """File on client but not server → to_upload."""
        client_entries = [
            ManifestEntry(
                relative_path="worklog_2024-01-15.txt",
                sha256="abc123" * 10 + "abcd",
                modified_at=datetime(2024, 1, 15, 12, 0),
            )
        ]
        client_manifest = FileManifest(entries=client_entries)
        server_manifest = FileManifest(entries=[])

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(client_manifest, server_manifest)

        assert len(diff.to_upload) == 1
        assert diff.to_upload[0] == "worklog_2024-01-15.txt"

    def test_server_has_new_file(self):
        """File on server but not client → to_download."""
        server_entries = [
            ManifestEntry(
                relative_path="worklog_2024-01-16.txt",
                sha256="def456" * 10 + "defg",
                modified_at=datetime(2024, 1, 16, 12, 0),
            )
        ]
        client_manifest = FileManifest(entries=[])
        server_manifest = FileManifest(entries=server_entries)

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(client_manifest, server_manifest)

        assert len(diff.to_download) == 1
        assert diff.to_download[0] == "worklog_2024-01-16.txt"

    def test_conflict_last_write_wins(self):
        """Same file modified on both sides → last-write-wins."""
        client_entry = ManifestEntry(
            relative_path="worklog_2024-01-15.txt",
            sha256="client_hash_" + "x" * 52,
            modified_at=datetime(2024, 1, 15, 14, 0),  # newer
        )
        server_entry = ManifestEntry(
            relative_path="worklog_2024-01-15.txt",
            sha256="server_hash_" + "y" * 52,
            modified_at=datetime(2024, 1, 15, 12, 0),  # older
        )

        service = RemoteSyncService(storage_root="/tmp")
        diff = service.compare_manifests(
            FileManifest(entries=[client_entry]),
            FileManifest(entries=[server_entry]),
        )

        # Client is newer → upload to server
        assert len(diff.to_upload) == 1
        assert len(diff.conflicts) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_remote_sync.py -v
```

- [ ] **Step 3: Implement RemoteSyncService**

```python
# web/services/remote_sync_service.py
# ABOUTME: Sync protocol logic for manifest comparison and file-level sync
# ABOUTME: Handles manifest generation, diff computation, and conflict detection

import hashlib
import os
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class ManifestEntry:
    """Single file entry in a sync manifest."""
    relative_path: str
    sha256: str
    modified_at: datetime


@dataclass
class FileManifest:
    """Complete file manifest for sync comparison."""
    entries: List[ManifestEntry] = field(default_factory=list)


@dataclass
class SyncDiff:
    """Result of comparing two manifests."""
    to_upload: List[str] = field(default_factory=list)    # client → server
    to_download: List[str] = field(default_factory=list)  # server → client
    conflicts: List[str] = field(default_factory=list)    # modified on both


class RemoteSyncService:
    """Handles sync protocol logic."""

    def __init__(self, storage_root: str):
        self.storage_root = Path(storage_root)

    def generate_manifest(self, user_id: str) -> FileManifest:
        """Generate file manifest for a user's journal files."""
        user_root = self.storage_root / user_id if user_id != "local" else self.storage_root
        entries = []

        for root, _dirs, files in os.walk(user_root):
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                file_path = Path(root) / filename
                relative = file_path.relative_to(user_root)

                content = file_path.read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)

                entries.append(ManifestEntry(
                    relative_path=str(relative),
                    sha256=sha256,
                    modified_at=modified_at,
                ))

        return FileManifest(entries=entries)

    def compare_manifests(
        self, client: FileManifest, server: FileManifest
    ) -> SyncDiff:
        """Compare client and server manifests to determine sync actions."""
        client_map = {e.relative_path: e for e in client.entries}
        server_map = {e.relative_path: e for e in server.entries}

        diff = SyncDiff()

        # Files on client but not server → upload
        for path in client_map:
            if path not in server_map:
                diff.to_upload.append(path)

        # Files on server but not client → download
        for path in server_map:
            if path not in client_map:
                diff.to_download.append(path)

        # Files on both with different hashes → conflict (last-write-wins)
        for path in client_map:
            if path in server_map:
                c = client_map[path]
                s = server_map[path]
                if c.sha256 != s.sha256:
                    diff.conflicts.append(path)
                    if c.modified_at >= s.modified_at:
                        diff.to_upload.append(path)
                    else:
                        diff.to_download.append(path)

        return diff
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_remote_sync.py -v
```

Expected: PASS.

- [ ] **Step 5: Create sync API router**

```python
# web/api/remote_sync.py
# ABOUTME: API endpoints for the sync protocol (manifest, upload, download)
# ABOUTME: Server-side endpoints that sync clients connect to

from fastapi import APIRouter, Request, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/api/remote-sync", tags=["sync"])


class ManifestEntryModel(BaseModel):
    relative_path: str
    sha256: str
    modified_at: datetime


class ManifestRequest(BaseModel):
    entries: List[ManifestEntryModel]
    last_sync_at: Optional[datetime] = None


class SyncDiffResponse(BaseModel):
    to_upload: List[str]
    to_download: List[str]
    conflicts: List[str]


@router.post("/manifest", response_model=SyncDiffResponse)
async def compare_manifest(manifest: ManifestRequest, request: Request):
    """Compare client manifest with server state, return diff."""
    sync_service = request.app.state.remote_sync_service
    user_id = getattr(request.state, 'user_id', 'local')

    from web.services.remote_sync_service import FileManifest, ManifestEntry
    client_manifest = FileManifest(
        entries=[
            ManifestEntry(
                relative_path=e.relative_path,
                sha256=e.sha256,
                modified_at=e.modified_at,
            )
            for e in manifest.entries
        ]
    )

    server_manifest = sync_service.generate_manifest(user_id)
    diff = sync_service.compare_manifests(client_manifest, server_manifest)

    return SyncDiffResponse(
        to_upload=diff.to_upload,
        to_download=diff.to_download,
        conflicts=diff.conflicts,
    )


@router.post("/upload")
async def upload_file(
    relative_path: str,
    file: UploadFile = File(...),
    request: Request = None,
):
    """Upload a file from client to server."""
    sync_service = request.app.state.remote_sync_service
    user_id = getattr(request.state, 'user_id', 'local')

    content = await file.read()
    sync_service.save_file(user_id, relative_path, content)
    return {"status": "ok", "path": relative_path}


@router.get("/download")
async def download_file(relative_path: str, request: Request):
    """Download a file from server to client."""
    sync_service = request.app.state.remote_sync_service
    user_id = getattr(request.state, 'user_id', 'local')

    file_path = sync_service.get_file_path(user_id, relative_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(path=str(file_path), filename=file_path.name)


@router.post("/complete")
async def sync_complete(request: Request):
    """Mark sync as complete, update last_sync_at."""
    user_id = getattr(request.state, 'user_id', 'local')
    # Update last_sync_at in database
    return {"status": "ok", "synced_at": datetime.utcnow().isoformat()}
```

- [ ] **Step 6: Add save_file and get_file_path to RemoteSyncService**

```python
# Add to RemoteSyncService class:

def save_file(self, user_id: str, relative_path: str, content: bytes) -> Path:
    """Save uploaded file to user's storage."""
    user_root = self.storage_root / user_id if user_id != "local" else self.storage_root
    file_path = user_root / relative_path
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)
    return file_path

def get_file_path(self, user_id: str, relative_path: str) -> Path:
    """Get absolute path for a user's file."""
    user_root = self.storage_root / user_id if user_id != "local" else self.storage_root
    return user_root / relative_path
```

- [ ] **Step 7: Include router in web/app.py**

```python
# In WorkJournalWebApp, add to route includes:
from web.api import remote_sync
self.app.include_router(remote_sync.router)

# In startup, initialize sync service if in server mode:
if self.config.server.mode == "server":
    from web.services.remote_sync_service import RemoteSyncService
    self.app.state.remote_sync_service = RemoteSyncService(
        storage_root=self.config.server.storage_root
    )
```

- [ ] **Step 8: Run tests**

```bash
pytest tests/test_remote_sync.py -v
```

- [ ] **Step 9: Commit**

```bash
git add web/api/remote_sync.py web/services/remote_sync_service.py web/app.py tests/test_remote_sync.py
git commit -m "feat: add sync API endpoints and manifest comparison service"
```

---

### Task D2: Sync Client

**Files:**
- Create: `sync_client.py` — HTTP client for sync protocol
- Create: `tests/test_sync_client.py`

- [ ] **Step 1: Write failing test**

```python
# tests/test_sync_client.py
"""Tests for sync client."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from sync_client import SyncClient


class TestSyncClient:
    def test_init_with_config(self):
        """SyncClient initializes with remote URL and token."""
        client = SyncClient(
            remote_url="https://journal.example.com",
            auth_token="test-token",
            local_root="/home/user/worklogs",
        )
        assert client.remote_url == "https://journal.example.com"
        assert client.auth_token == "test-token"

    def test_build_headers(self):
        """Client includes auth token in request headers."""
        client = SyncClient(
            remote_url="https://journal.example.com",
            auth_token="test-token",
            local_root="/tmp",
        )
        headers = client._build_headers()
        assert headers["X-API-Key"] == "test-token"

    @pytest.mark.asyncio
    async def test_generate_local_manifest(self, tmp_path):
        """Client generates manifest from local files."""
        journal_file = tmp_path / "worklog_2024-01-15.txt"
        journal_file.write_text("Work notes.")

        client = SyncClient(
            remote_url="https://journal.example.com",
            auth_token="test-token",
            local_root=str(tmp_path),
        )
        manifest = client.generate_local_manifest()
        assert len(manifest.entries) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_sync_client.py -v
```

- [ ] **Step 3: Implement sync client**

```python
# sync_client.py
# ABOUTME: HTTP client for syncing local journal files with a remote server
# ABOUTME: Implements the manifest-compare-upload-download sync protocol

import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List

import requests

from web.services.remote_sync_service import FileManifest, ManifestEntry, SyncDiff


class SyncClient:
    """Client for syncing local journal files with a remote server."""

    def __init__(
        self,
        remote_url: str,
        auth_token: str,
        local_root: str,
        timeout: int = 30,
    ):
        self.remote_url = remote_url.rstrip("/")
        self.auth_token = auth_token
        self.local_root = Path(local_root)
        self.timeout = timeout

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers with authentication."""
        return {
            "X-API-Key": self.auth_token,
            "User-Agent": "WorkJournalMaker-SyncClient/1.0",
        }

    def generate_local_manifest(self) -> FileManifest:
        """Generate manifest from local journal files."""
        entries = []
        for root, _dirs, files in os.walk(self.local_root):
            for filename in files:
                if not filename.endswith('.txt'):
                    continue
                file_path = Path(root) / filename
                relative = file_path.relative_to(self.local_root)
                content = file_path.read_bytes()
                sha256 = hashlib.sha256(content).hexdigest()
                modified_at = datetime.fromtimestamp(file_path.stat().st_mtime)
                entries.append(ManifestEntry(
                    relative_path=str(relative),
                    sha256=sha256,
                    modified_at=modified_at,
                ))
        return FileManifest(entries=entries)

    def sync(self) -> Dict[str, int]:
        """Execute full sync cycle: manifest → upload → download → complete."""
        # Step 1: Generate local manifest and send to server
        local_manifest = self.generate_local_manifest()
        diff = self._send_manifest(local_manifest)

        uploaded = 0
        downloaded = 0

        # Step 2: Upload files server needs
        for path in diff.get("to_upload", []):
            self._upload_file(path)
            uploaded += 1

        # Step 3: Download files we need
        for path in diff.get("to_download", []):
            self._download_file(path)
            downloaded += 1

        # Step 4: Mark sync complete
        self._complete_sync()

        return {
            "uploaded": uploaded,
            "downloaded": downloaded,
            "conflicts": len(diff.get("conflicts", [])),
        }

    def _send_manifest(self, manifest: FileManifest) -> dict:
        """Send local manifest to server, get back diff."""
        payload = {
            "entries": [
                {
                    "relative_path": e.relative_path,
                    "sha256": e.sha256,
                    "modified_at": e.modified_at.isoformat(),
                }
                for e in manifest.entries
            ]
        }
        response = requests.post(
            f"{self.remote_url}/api/remote-sync/manifest",
            json=payload,
            headers=self._build_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _upload_file(self, relative_path: str) -> None:
        """Upload a single file to the server."""
        file_path = self.local_root / relative_path
        with open(file_path, "rb") as f:
            response = requests.post(
                f"{self.remote_url}/api/remote-sync/upload",
                params={"relative_path": relative_path},
                files={"file": (file_path.name, f)},
                headers=self._build_headers(),
                timeout=self.timeout,
            )
        response.raise_for_status()

    def _download_file(self, relative_path: str) -> None:
        """Download a single file from the server."""
        response = requests.get(
            f"{self.remote_url}/api/remote-sync/download",
            params={"relative_path": relative_path},
            headers=self._build_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()

        file_path = self.local_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(response.content)

    def _complete_sync(self) -> None:
        """Mark sync as complete on server."""
        response = requests.post(
            f"{self.remote_url}/api/remote-sync/complete",
            headers=self._build_headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
```

- [ ] **Step 4: Run tests**

```bash
pytest tests/test_sync_client.py -v
```

Expected: PASS.

- [ ] **Step 5: Write integration test for full sync flow**

```python
# tests/test_sync_integration.py
"""Integration test for full sync flow between client and server."""
import pytest
from pathlib import Path
from web.services.remote_sync_service import RemoteSyncService


class TestSyncIntegration:
    def test_full_sync_flow(self, tmp_path):
        """End-to-end: client and server exchange files via manifests."""
        # Setup client and server directories
        client_root = tmp_path / "client"
        server_root = tmp_path / "server" / "local"
        client_root.mkdir(parents=True)
        server_root.mkdir(parents=True)

        # Client has file A, server has file B
        (client_root / "worklog_2024-01-15.txt").write_text("Client entry")
        (server_root / "worklog_2024-01-16.txt").write_text("Server entry")

        # Generate manifests
        client_service = RemoteSyncService(storage_root=str(client_root.parent))
        server_service = RemoteSyncService(storage_root=str(server_root.parent))

        # Use client_root directly for manifest since user_id handling
        client_manifest = client_service.generate_manifest(user_id="client")
        server_manifest = server_service.generate_manifest(user_id="local")

        # Compare
        diff = server_service.compare_manifests(client_manifest, server_manifest)

        # Client should upload file A, download file B
        assert "worklog_2024-01-15.txt" in diff.to_upload
        assert "worklog_2024-01-16.txt" in diff.to_download
```

- [ ] **Step 6: Run integration test**

```bash
pytest tests/test_sync_integration.py -v
```

- [ ] **Step 7: Commit**

```bash
git add sync_client.py tests/test_sync_client.py tests/test_sync_integration.py
git commit -m "feat: add sync client for local-to-server sync protocol"
```

---

## Track E: Docker Deployment

> **Depends on Tracks C and D.** Final phase.

### Task E1: Docker Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `docker-compose.server.yml`
- Create: `tests/test_docker_config.py`

- [ ] **Step 1: Write test for Dockerfile syntax**

```python
# tests/test_docker_config.py
"""Tests for Docker configuration files."""
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


class TestDockerFiles:
    def test_dockerfile_exists(self):
        assert (PROJECT_ROOT / "Dockerfile").exists()

    def test_dockerfile_has_required_instructions(self):
        content = (PROJECT_ROOT / "Dockerfile").read_text()
        assert "FROM python:" in content
        assert "EXPOSE" in content
        assert "CMD" in content or "ENTRYPOINT" in content

    def test_docker_compose_exists(self):
        assert (PROJECT_ROOT / "docker-compose.yml").exists()

    def test_docker_compose_server_exists(self):
        assert (PROJECT_ROOT / "docker-compose.server.yml").exists()
```

- [ ] **Step 2: Create Dockerfile**

```dockerfile
# ABOUTME: Production container for WorkJournalMaker server mode
# ABOUTME: Runs FastAPI with uvicorn, persists data via volume mount

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data/users

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/health/')" || exit 1

# Run in server mode
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 3: Create docker-compose.yml**

```yaml
# ABOUTME: Base Docker Compose for local development
# ABOUTME: Runs the app in local mode with SQLite

services:
  app:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/data
    environment:
      - WJS_SERVER_MODE=local
```

- [ ] **Step 4: Create docker-compose.server.yml**

```yaml
# ABOUTME: Docker Compose override for server mode deployment
# ABOUTME: Enables auth, configures multi-user storage

services:
  app:
    environment:
      - WJS_SERVER_MODE=server
      - WJS_AUTH_ENABLED=true
      - WJS_AUTH_PROVIDER=google
      - WJS_STORAGE_ROOT=/data/users/
    volumes:
      - journal-data:/data
      - ./config.yaml:/app/config.yaml:ro

volumes:
  journal-data:
```

- [ ] **Step 5: Run tests**

```bash
pytest tests/test_docker_config.py -v
```

- [ ] **Step 6: Commit**

```bash
git add Dockerfile docker-compose.yml docker-compose.server.yml tests/test_docker_config.py
git commit -m "feat: add Docker configuration for server mode deployment"
```

---

## Summary: Task Dependencies for Subagent Dispatch

```
INDEPENDENT (start immediately, parallel):
  Subagent 1: Task A1 (rewrite spec)
  Subagent 2: Task A2 (create icons)
  Subagent 3: Task B1 (multi-user schema)

AFTER A1:
  Subagent 4: Task A3 (simplify build system)

AFTER A2 + A3:
  Subagent 5: Task A4 (verify working build)

AFTER A4 (parallel):
  Subagent 6: Task A5 (macOS installer)
  Subagent 7: Task A6 (Windows installer)

AFTER B1:
  Subagent 8: Task B2 (user-scoped services)

AFTER B2:
  Subagent 9: Task B3 (server config)

AFTER A5 + A6:
  Subagent 10: Task A7 (CI/CD workflow)

AFTER B3 (parallel):
  Subagent 11: Task C1 (auth)
  Subagent 12: Task D1 (sync API)

AFTER D1:
  Subagent 13: Task D2 (sync client)

AFTER C1 + D2:
  Subagent 14: Task E1 (Docker)
```

Total: 14 tasks across 5 tracks, with up to 3 subagents running in parallel at peak.
