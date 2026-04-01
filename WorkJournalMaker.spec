# ABOUTME: PyInstaller build specification for the WorkJournalMaker desktop application.
# ABOUTME: Bundles server_runner.py as entry point with web assets and desktop modules.
# -*- mode: python ; coding: utf-8 -*-

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
