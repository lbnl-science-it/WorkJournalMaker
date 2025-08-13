# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for WorkJournalMaker
# Generated automatically by build_config.py


a = Analysis(
    ['server_runner.py'],
    pathex=['/Users/TYFong/code/WorkJournalMaker'],
    binaries=[],
    datas=[
        ('/Users/TYFong/code/WorkJournalMaker/web/static', 'web/static'),
    ('/Users/TYFong/code/WorkJournalMaker/web/templates', 'web/templates')
    ],
    hiddenimports=[
        # Web application modules (CRITICAL)
        'web',
        'web.app',
        'web.api',
        'web.api.calendar',
        'web.api.entries',
        'web.api.health',
        'web.api.settings',
        'web.api.summarization',
        'web.api.sync',
        'web.services',
        'web.services.calendar_service',
        'web.services.entry_manager',
        'web.services.web_summarizer',
        'web.models',
        'web.models.journal',
        'web.models.responses',
        'web.models.settings',
        'web.database',
        'web.middleware',
        
        # Uvicorn server components
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        
        # FastAPI components
        'fastapi.routing',
        'fastapi.responses',
        'fastapi.encoders',
        'fastapi.exceptions',
        
        # Starlette components
        'starlette.routing',
        'starlette.responses',
        'starlette.middleware',
        'starlette.staticfiles',
        
        # SQLAlchemy components
        'sqlalchemy.ext.declarative',
        'sqlalchemy.sql.default_comparator',
        'aiosqlite',
        
        # Template engine
        'jinja2.ext',
        
        # Google GenAI (if used)
        'google.genai',
        'google.genai.models',
        'google.genai.client',
        'google.auth',
        'google.oauth2',
        
        # AWS Bedrock (if used)
        'boto3',
        'botocore',
        'botocore.client',
        'botocore.session'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
    '_tkinter',
    'matplotlib',
    'matplotlib.pyplot',
    'PyQt5',
    'PyQt6',
    'PySide2',
    'PySide6',
    'pytest',
    'pytest_cov',
    'pytest_mock',
    'coverage',
    'black',
    'flake8',
    'mypy',
    'sphinx',
    'jupyter',
    'notebook',
    'ipython'
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='WorkJournalMaker',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)