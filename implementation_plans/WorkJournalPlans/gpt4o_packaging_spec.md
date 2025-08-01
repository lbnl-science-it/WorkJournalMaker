# Developer-Ready Specification for WorkJournal Packaging

## 1. Overview
WorkJournal is a Python/FastAPI application that launches a local web server, presenting a browser UI for journaling and summarization. The goal is to deliver self-contained, double-clickable desktop packages (zip downloads) for:
- macOS 13 Ventura + (Apple Silicon only)
- Windows 11 (x64)

## 2. Functional Requirements
### 2.1 Installation / Launch
- **R1**: A single zip archive per OS hosted on the GitHub Release page (drafted automatically).
- **R2**: Users unzip anywhere and double-click the launcher: WorkJournal (mac) / WorkJournal.exe (win).
- **R3**: First launch prompts for server port (default 8000) → stored in config.
- **R4**: Subsequent launches skip prompt and open http://localhost:<port>.
- **R5**: Logs stream to rotating log file in user-data directory; no console window shown (use pythonw or flag for Windows).

### 2.2 Updates
- **R6**: Upgrades are manual with user data preserved in the home-directory data folder.

### 2.3 Platform Scope
- **R7**: macOS build is Apple-Silicon arm64 only.
- **R8**: Windows build targets Windows 11 x64 on GH hosted runner windows-2022.
- **R9**: No code-signing or notarization initially; users bypass OS warnings.

## 3. Architecture & Packaging Choices
### 3.1 Bundler
- PyInstaller single-folder mode.
- One .spec file controlling hidden-imports, datas, runtime-hook adding site-packages to sys.path, arm64 flag for mac.

### 3.2 Launcher GUI
- Tkinter for cross-platform minimal UI.
- Workflow:
  - Check ~/WorkJournal/config.json or %APPDATA%\\WorkJournal\\config.json.
  - If absent → show PortPromptDialog(default=8000).
  - Persist {"port": 8000}.
  - Spawn subprocess [runtime/python, -m, server_runner, --port <p>] with stdout/err redirected to log file.
  - Wait 1 s, then webbrowser.open_new_tab() to URL.
  - Exit launcher.

### 3.3 Folder Layout after Build
- WorkJournal-mac-arm64.zip
  - WorkJournal/
    - WorkJournal
    - runtime/ (private Python)
    - resources/ (templates, static, etc.)
    - launcher_gui.py (embedded in exe by --add-data)
    - README.txt

## 4. Data Handling Policy
- **D1**: User data root:
  - mac: ~/WorkJournal/
  - win: %APPDATA%\\WorkJournal\\

- **D2**: Sub-dirs:
  - db: SQLite journal database(s)
  - config: config.json (port + future prefs)
  - logs: rotating ‑YYYY-MM-DD.log (10 MB, keep 7)

- **D3**: Packaging scripts must not write inside application folder post-build; resolved via platformdirs library.

## 5. Error Handling Strategies
### E1 Launcher-level errors:
- Port in use → show error dialog “Port 8000 in use – choose another”, reopen port prompt.
- Server exits <5 s → capture stderr to latest log, show “Server failed to start; see logs”.

### E2 Server-level errors (FastAPI):
- Global exception handler returns JSON with error + request id; logs full stack trace.
- Uncaught fatal errors cause uvicorn exit; launcher does not respawn automatically.

### E3 File-system write failures log and surface in browser UI toast.

## 6. Continuous Integration / Delivery
### 6.1 GitHub Actions Workflow (.github/workflows/release.yml)
- Strategy: matrix { os: [macos-13, windows-2022] }
- Steps:
  - Checkout
  - Setup Python 3.11
  - Install requirements and PyInstaller
  - Run pytest
  - Package using PyInstaller
  - Zip and upload artifacts
  - Create draft release

### 6.2 Tagging Procedure
- Git tag -a vX.Y.Z -m "Release vX.Y.Z"
- Git push --tags

## 7. Testing Plan
### 7.1 Unit Tests
- All existing pytest suites must pass in CI.
- Add tests for launcher_gui: port config persistence and process start.

### 7.2 Integration Tests (CI)
- Post-build, run built executable in headless mode with `--test` flag.
- Curl http://localhost:<port>/api/health returns 200.

### 7.3 Manual Acceptance Checklist
- Unzip, double-click launcher.
- Port prompt appears with 8000 -> OK.
- Browser opens on journal UI; can create entry, refresh, data persists.
- Quit server and relaunch; prompt skipped; data still present.
- Verify logs written to user data folder.
- Upgrade test: unzip new version in different folder, launch, data present.

## 8. Open Items & Road-Map
- Code-signing & notarization pipeline.
- Auto-update mechanism.
- Universal-2 mac build if Intel demand resurfaces.
- Optional nightly builds workflow for QA.

This specification is intended for immediate implementation of packaging, launcher, and CI/CD automation.