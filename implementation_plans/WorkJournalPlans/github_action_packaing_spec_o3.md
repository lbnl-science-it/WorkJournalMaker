Developer-Ready Specification  
WorkJournal – Cross-Platform Stand-Alone Desktop Package  
Version 1.0 (draft)

────────────────────────────────────────────────────────
# 1  Overview
WorkJournal is currently a Python/FastAPI code-base that runs a local web server presenting a browser UI for daily journaling and summarization.  
Goal: deliver self-contained, double-clickable desktop packages (zip downloads) for:
• macOS 13 Ventura + (Apple Silicon only)  
• Windows 11 (x64)

The package must include its own Python runtime and all dependencies, start the FastAPI server in the background, open the browser, and preserve user data across upgrades.

────────────────────────────────────────────────────────
# 2  Functional Requirements
## 2.1 Installation / Launch
R1  A single zip archive per OS hosted on the GitHub Release page (drafted automatically).  
R2  Users unzip anywhere and double-click the launcher: WorkJournal (mac) / WorkJournal.exe (win).  
R3  First launch shows a minimal GUI prompt asking for the server port (default 8000) → stored in config.  
R4  Subsequent launches skip the prompt, start the server, and open http://localhost:<port>.  
R5  Logs stream to a rotating log file in the user-data directory; no console window is shown (windows: use pythonw or flag).  

## 2.2 Updates
R6  Upgrades are manual: user downloads newer zip and replaces old folder. Existing user data must remain untouched in the home-directory data folder.

## 2.3 Platform Scope
R7  macOS build is Apple-Silicon arm64 only.  
R8  Windows build targets Windows 11 x64 on GH hosted runner windows-2022.  
R9  No code-signing or notarization initially; users will bypass OS warnings (road-map item).

────────────────────────────────────────────────────────
# 3  Architecture & Packaging Choices
## 3.1 Bundler  
• PyInstaller single-folder mode.  
• One .spec file in /packaging/ controlling: hidden-imports, datas, runtime-hook adding site-packages to sys.path, arm64 flag for mac.

## 3.2 Launcher GUI (launcher_gui.py)  
• Tkinter (std-lib) for cross-platform minimal UI.  
• Workflow:  
    ‑ Check ~/WorkJournal/config.json or %APPDATA%\WorkJournal\config.json.  
    ‑ If absent → show PortPromptDialog(default=8000).  
    ‑ Persist {"port": 8000}.  
    ‑ Spawn subprocess [runtime/python, -m, server_runner, --port <p>] with stdout/err redirected to log file.  
    ‑ Wait 1 s, then webbrowser.open_new_tab() to URL.  
    ‑ Exit launcher.

## 3.3 Folder Layout after Build
WorkJournal-mac-arm64.zip  
  └─ WorkJournal/  
       ├─ WorkJournal                 # Mach-O executable stub created by pyinstaller  
       ├─ runtime/ (private Python)  
       ├─ resources/ (templates, static, etc.)  
       ├─ launcher_gui.py (embedded in exe by --add-data)  
       └─ README.txt  

Same layout for Windows with .exe.

────────────────────────────────────────────────────────
# 4  Data Handling Policy
D1  User data root:  
    • mac  : ~/WorkJournal/  
    • win  : %APPDATA%\WorkJournal\  

D2  Sub-dirs:  
    /db   SQLite journal database(s)  
    /config config.json (port + future prefs)  
    /logs  rotating ‑YYYY-MM-DD.log (10 MB, keep 7)  

D3  Packaging scripts must never write inside the application folder after build; all write paths are resolved via platformdirs library (bundled).

────────────────────────────────────────────────────────
# 5  Error Handling Strategies
E1  Launcher-level errors:  
    • If port already in use → show error dialog “Port 8000 in use – choose another”, reopen port prompt.  
    • If server subprocess exits <5 s → capture stderr to latest log, show “Server failed to start; see logs”.  

E2  Server-level errors (FastAPI):  
    • Global exception handler returns JSON with error + request id; logs full stack trace.  
    • Uncaught fatal errors cause uvicorn to exit; launcher does not respawn automatically (future improvement).  

E3  Any file-system write failures log and surface in browser UI toast.

────────────────────────────────────────────────────────
# 6  Continuous Integration / Delivery
## 6.1 GitHub Actions Workflow (.github/workflows/release.yml)
jobs:
  build-matrix:
    strategy: matrix { os: [macos-13, windows-2022] }
    on: push tags matching v*
    steps:
      ‑ checkout
      ‑ setup-python 3.11
      ‑ pip install -r requirements.txt pyinstaller platformdirs
      ‑ run pytest
      ‑ pyinstaller --noconfirm --clean --one-dir --name WorkJournal \
            --add-data "web:resources/web" packaging/pyinstaller.spec
      ‑ zip -r WorkJournal-${{ matrix.os }}.zip dist/WorkJournal
      ‑ upload-artifact name=artifact-${{ matrix.os }}
  create-draft-release:
    needs: build-matrix
    runs-on: ubuntu-latest
    steps:
      ‑ download-artifact
      ‑ gh release create ${{ github.ref_name }} \
           --draft \
           -t "WorkJournal ${{ github.ref_name }}" \
           -n "" \
           dist/WorkJournal-macos-13.zip#WorkJournal-mac-arm64.zip \
           dist/WorkJournal-windows-2022.zip#WorkJournal-win-x64.zip

## 6.2 Tagging Procedure
  git tag -a vX.Y.Z -m "Release vX.Y.Z"
  git push --tags

────────────────────────────────────────────────────────
# 7  Testing Plan
## 7.1 Unit Tests  
    • All existing pytest suites must pass in CI.  
    • Add tests for launcher_gui: port config persistence and process start (use subprocess + mocks).  

## 7.2 Integration Tests (CI)  
    • Post-build, run built executable in headless mode with `--test` flag that starts server, waits for “Running on”, then exits.  
    • Curl http://localhost:<port>/api/health returns 200.  

## 7.3 Manual Acceptance Checklist  
    macOS & Windows:  
      1. Unzip, double-click launcher.  
      2. Port prompt appears with 8000 -> OK.  
      3. Browser opens on journal UI; can create entry, refresh, data persists.  
      4. Quit server (Cmd-Q / tray exit) and relaunch; prompt skipped; data still present.  
      5. Verify logs written to user data folder.  
      6. Upgrade test: unzip new version in different folder, launch, data present.

────────────────────────────────────────────────────────
# 8  Open Items & Road-Map
• Code-signing & notarization pipeline.  
• Auto-update mechanism (Sparkle/WinSparkle or custom).  
• Universal-2 mac build if Intel demand resurfaces.  
• Optional nightly builds workflow for QA.

This specification supersedes prior high-level notes and is sufficient for a developer to implement packaging, launcher, and CI/CD automation immediately. All deviations require spec update & approval.