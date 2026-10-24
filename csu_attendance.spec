# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for the CSU Attendance kiosk.

Role in the system: turns the source tree into a folder that runs on a machine
that has never had Python installed. Hand-written and committed -- this is not a
generated artefact, and the three decisions below are the whole reason it
exists.

**The model pack is NOT bundled.** buffalo_l is about 300 MB of ONNX, and
PyInstaller would unpack every byte of it into a temporary directory on every
single launch. That turns a two-second start into thirty, and it is the
difference between a kiosk somebody uses and one they walk past. `models/` is
copied *beside* the executable instead (see build.bat) and found through
`config.MODEL_ROOT`, which is why `app/face_engine.py` passes `root=` to
FaceAnalysis explicitly -- insightface 1.0.1 does not read INSIGHTFACE_HOME
itself, so nothing else would point it at the external folder.

**Every non-code file goes through `config.resource_path`.** `style.qss` is the
only one today. A frozen build reads it out of `sys._MEIPASS`; a source run
reads it from the project tree. Anything that skips that helper works in
development and fails in the packaged app, which is the classic way a packaging
job loses a day.

**`.env` is not bundled either.** It holds the database password and the
administrator password, and a secret compiled into a distributable is a secret
no longer. `.env.example` ships next to the .exe and `app/ui/first_run.py`
offers to create the real one on first launch.

Build with::

    build.bat

or directly::

    pyinstaller csu_attendance.spec --noconfirm
"""

from pathlib import Path

from PyInstaller.utils.hooks import collect_all

APP_NAME = "CSU Attendance"

# SPECPATH is set by PyInstaller to the directory holding this file.
project_root = Path(SPECPATH)  # noqa: F821 - injected by PyInstaller

datas = []
binaries = []
hiddenimports = []

# PLAN.md names these two explicitly. Both load code and data at runtime in ways
# PyInstaller's static analysis cannot see: insightface resolves model classes by
# name, and onnxruntime ships native providers as loose DLLs.
for package in ("insightface", "onnxruntime"):
    package_datas, package_binaries, package_hiddenimports = collect_all(package)
    datas += package_datas
    binaries += package_binaries
    hiddenimports += package_hiddenimports

# The stylesheet, at the same relative path `config.resource_path` asks for.
datas += [(str(project_root / "app" / "ui" / "style.qss"), "app/ui")]
datas += [(str(project_root / "app" / "assets" / "csu_logo.png"), "app/assets")]
# PySide6 is handled by PyInstaller's bundled hooks; these are the pieces our
# code imports indirectly and that a minimal analysis can miss.
hiddenimports += [
    "PySide6.QtSvg",  # Qt loads it for icon rendering
    "pymysql",
    "docx",
    # SQLAlchemy resolves its dialect by URL string, so nothing statically
    # references this module and PyInstaller would otherwise leave it out --
    # producing a "Can't load plugin: sqlalchemy.dialects:mysql" at first launch.
    "sqlalchemy.dialects.mysql.pymysql",
]

# Not needed by the kiosk, and large. The calibration and evaluation scripts do
# use matplotlib, but they are development tools run from source during Phase 10
# -- they are not part of what stands in the corridor.
excludes = [
    "tkinter",
    "pytest",
    "matplotlib",
    "IPython",
    "notebook",
]


analysis = Analysis(  # noqa: F821 - injected by PyInstaller
    [str(project_root / "main.py")],
    pathex=[str(project_root)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    noarchive=False,
)

pyz = PYZ(analysis.pure)  # noqa: F821 - injected by PyInstaller

executable = EXE(  # noqa: F821 - injected by PyInstaller
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # console=True on purpose. A kiosk that fails to start must say why, and a
    # windowed build swallows the traceback -- which is how a packaging problem
    # becomes "it just closes" three days before a defense. Set it to False once
    # the build has been proven on the target machine.
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# COLLECT, not a one-file build. One-file unpacks the entire bundle to a temp
# directory on every launch, which for this dependency set is several seconds
# before any of our code runs -- and it puts `.env` somewhere the operator
# cannot find to edit.
collected = COLLECT(  # noqa: F821 - injected by PyInstaller
    executable,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=APP_NAME,
)
