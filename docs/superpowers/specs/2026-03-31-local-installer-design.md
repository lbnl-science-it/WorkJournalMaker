# Local Installer Design for WorkJournalMaker

## Overview

Package WorkJournalMaker as a native desktop application with one-click installers for macOS and Windows. Non-technical users should be able to download, install, and start journaling without encountering Python, terminals, or configuration files.

## Distribution Model

- Near-term: distribute to peers at LBNL via GitHub Releases
- Medium-term: open source release for organizations to self-host
- Long-term: NextCloud-style platform (self-hostable, or pay someone to host)

The local app is the primary product. A sync server is secondary infrastructure for backup and multi-device access.

## Approach: PyInstaller + Platform Installers

PyInstaller bundles Python + dependencies into a standalone executable. Platform-specific tools wrap it into native installers.

- **macOS:** PyInstaller → `.app` bundle → `create-dmg` → `.dmg`
- **Windows:** PyInstaller → directory with `.exe` → Inno Setup → `Setup.exe`

## Architecture

### Build Pipeline

```
Source Code
    |
    v
[PyInstaller] --- bundles Python + deps into standalone executable
    |
    +-- macOS: WorkJournalMaker.app/ (.app bundle)
    +-- Windows: WorkJournalMaker/ (directory with .exe)
    |
    v
[Platform Installer Tool]
    |
    +-- macOS: create-dmg -> WorkJournalMaker.dmg
    +-- Windows: Inno Setup -> WorkJournalMaker-Setup.exe
```

### Entry Point

`server_runner.py` is the packaged entry point. It:
1. Finds an available port (via `desktop/port_detector.py`)
2. Starts the FastAPI web server in a background thread (via `desktop/server_manager.py`)
3. Opens the user's default browser (via `desktop/browser_controller.py`)
4. Waits for shutdown signal

The `desktop/` package provides the runtime components. All modules in this package are retained as-is.

### macOS Specifics

**PyInstaller output:** A `.app` bundle with `--windowed` (no terminal) and `--onedir` mode.

**App bundle structure:**
```
WorkJournalMaker.app/
  Contents/
    MacOS/WorkJournalMaker        (executable)
    Resources/icon.icns           (app icon)
    Frameworks/                   (bundled libraries)
    Info.plist                    (app metadata)
```

**Installer:** `create-dmg` produces a `.dmg` disk image with drag-to-Applications UX.

**Code signing:** Not included for MVP. Users bypass Gatekeeper via right-click -> Open -> Open (one-time). Apple Developer account ($99/year) needed for signed releases later.

### Windows Specifics

**PyInstaller output:** A directory with `--windowed` (no console) and `--onedir` mode.

**Installer:** Inno Setup creates `WorkJournalMaker-Setup.exe` that:
- Installs to `C:\Program Files\WorkJournalMaker\`
- Creates Start Menu shortcut
- Optionally creates Desktop shortcut
- Registers uninstaller in "Add or Remove Programs"

**SmartScreen:** Not addressed for MVP. Users click "More info" -> "Run anyway" (one-time). Code signing certificate ($200-400/year) needed for signed releases later.

### CI/CD Release Pipeline

GitHub Actions automates building for both platforms. Triggered by pushing a version tag.

**Workflow:**
```
git tag v1.0.0 && git push --tags
         |
         v
  GitHub Actions triggered
         |
    +----+----+
    v         v
  macOS     Windows
  runner     runner
    |         |
    v         v
PyInstaller  PyInstaller
    |         |
    v         v
create-dmg   Inno Setup
    |         |
    v         v
  .dmg      Setup.exe
    |         |
    +----+----+
         v
  GitHub Release
  (both artifacts attached)
```

**Workflow steps per platform:**
1. Check out code
2. Set up Python, install dependencies
3. Run tests (sanity check)
4. Run PyInstaller with `.spec` file
5. Run platform installer tool
6. Upload artifact to GitHub Release

**Local builds** remain available via `python scripts/build.py --clean` for development iteration (produces executable in `dist/`, skips installer creation).

## Existing Code Assessment

### Retain (desktop/ runtime components)

All modules in `desktop/` are well-structured and handle the runtime lifecycle correctly:
- `desktop_app.py` — orchestrates startup/shutdown
- `server_manager.py` — uvicorn lifecycle in background thread
- `browser_controller.py` — cross-platform browser opening
- `platform_compat.py` — macOS/Windows/Linux path, process, signal abstractions
- `port_detector.py` — port availability checking
- `readiness_checker.py` — HTTP/TCP health checks with backoff

`server_runner.py` — solid entry point with CLI args and signal handling. Retained as-is.

### Rework (build system)

- `WorkJournalMaker.spec` — rewrite to point to `server_runner.py`, include `desktop/` and `web/` packages, use `--onedir` + `--windowed`, add icon
- `build_system/local_builder.py` — simplify to thin wrapper around `pyinstaller WorkJournalMaker.spec`
- `build_system/build_config.py` — remove `PyInstallerSpecGenerator` class; retain `BuildConfig` for asset/import discovery methods
- `scripts/build.py` — simplify to match reduced `local_builder.py`

## Project Structure Changes

### Files to Fix

| File | Change |
|---|---|
| `WorkJournalMaker.spec` | Rewrite: `server_runner.py` entry point, include `desktop/` + `web/`, `--onedir` + `--windowed`, icon |
| `build_system/build_config.py` | Remove `PyInstallerSpecGenerator` class entirely. Retain `BuildConfig` class for its `get_hidden_imports()`, `get_excluded_modules()`, and `get_static_assets()` methods, which the `.spec` file references. |
| `build_system/local_builder.py` | Simplify: thin wrapper around PyInstaller invocation |
| `scripts/build.py` | Simplify to match reduced local_builder |

### Files to Create

| File | Purpose |
|---|---|
| `assets/icon.icns` | macOS app icon |
| `assets/icon.ico` | Windows app icon |
| `assets/Info.plist.template` | macOS app metadata (version injected at build time) |
| `installer/macos/create-dmg.sh` | Script wrapping `create-dmg` invocation |
| `installer/windows/installer.iss` | Inno Setup script for Windows installer |
| `.github/workflows/release.yml` | CI/CD release pipeline |

### Resulting Structure

```
WorkJournalMaker/
  desktop/                      (KEEP: runtime components)
  assets/                       (NEW: icons, metadata templates)
    icon.icns
    icon.ico
    Info.plist.template
  installer/                    (NEW: platform installer configs)
    macos/create-dmg.sh
    windows/installer.iss
  scripts/
    build.py                    (SIMPLIFIED)
  build_system/
    local_builder.py            (SIMPLIFIED)
  .github/workflows/
    release.yml                 (NEW: CI/CD)
  WorkJournalMaker.spec         (REWRITTEN)
  server_runner.py              (KEEP: entry point)
```

## Relationship to Sync Plan

This work is independent of the local-first sync plan (Phases 1-7). It does not depend on multi-user schema, auth, or sync protocol. The only prerequisite is a working web app, which already exists.

Suggested placement: **Phase 8** in the overall plan, executable in parallel with Phases 1-7.

## Scope Boundaries (YAGNI)

Not included in this design:
- Code signing / notarization (add when distributing publicly)
- Auto-update mechanism (manual updates for now)
- Background service / system tray (manual launch only)
- Linux packaging (add when there's demand)
- Homebrew formula or pip install path (add later for developer audience)

## User Experience

### macOS Install Flow
1. Download `WorkJournalMaker.dmg` from GitHub Releases
2. Open the DMG
3. Drag WorkJournalMaker to Applications
4. First launch: right-click -> Open -> Open (bypasses Gatekeeper once)
5. App opens browser to local journal UI

### Windows Install Flow
1. Download `WorkJournalMaker-Setup.exe` from GitHub Releases
2. Run the installer
3. First launch: click "More info" -> "Run anyway" (bypasses SmartScreen once)
4. Click Next through the wizard
5. Launch from Start Menu or Desktop shortcut
6. App opens browser to local journal UI
