"""Entry point: build the QApplication, pick a camera, show the kiosk.

Role in the system: the only module that constructs the application object and
decides what the user sees first. Everything it does is startup sequencing --
there is no business logic here, and there should never be any.

Run it with::

    python main.py                 # remembered camera, fullscreen if configured
    python main.py --windowed      # windowed, for development
    python main.py --camera 1      # override the remembered index, without saving it
    python main.py --select-camera # force the picker open

The first-run path matters: a terminal that has never chosen a camera has
nothing to show, so the picker opens before the window rather than leaving
someone staring at a black screen. Once chosen, the index lives in QSettings and
this never asks again.

PLAN.md puts a splash screen here, around `face_engine.warm_up()`, so the model
pack is loaded before the first person walks up rather than during their scan --
the "first recognition takes 10+ seconds" failure mode. The warm-up happens, but
on the recognition worker's own thread (`RecognitionWorker.prepare`) rather than
behind a modal splash: the camera preview is live within a second of launch, and
covering it with a splash would hide the one thing worth watching while the model
loads. The kiosk shows "Loading face recognition..." over live video instead, and
does not dispatch a frame until the worker says it is ready.
"""

from __future__ import annotations

import argparse
import logging
import sys

from PySide6.QtWidgets import QApplication, QDialog

from app import config
from app.config import machine_settings
from app.ui import first_run, theme
from app.ui.camera_dialog import CameraSelectDialog
from app.ui.kiosk_window import KioskWindow

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CSU Attendance Monitoring System")
    parser.add_argument(
        "--camera",
        type=int,
        default=None,
        help="Use this camera index for this run only; does not change the saved choice.",
    )
    parser.add_argument(
        "--select-camera",
        action="store_true",
        help="Open the camera picker on startup even if a camera is already saved.",
    )
    parser.add_argument(
        "--windowed",
        action="store_true",
        help="Start windowed instead of fullscreen.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        help="Python logging level (DEBUG, INFO, WARNING). Default INFO.",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip the first-run configuration, model and database checks.",
    )
    return parser.parse_args(argv)


def resolve_camera_index(args: argparse.Namespace) -> int | None:
    """Decide which camera to start on, asking the operator if necessary.

    Returns None only when the picker was cancelled with nothing already saved,
    which the caller treats as "start with no video" rather than as an error --
    the operator may be trying to reach the picker again from inside the window.
    """
    if args.camera is not None:
        logger.info("Camera index %s forced on the command line", args.camera)
        return args.camera

    saved = machine_settings.camera_index

    if saved is not None and not args.select_camera:
        return saved

    if saved is None:
        logger.info("No camera saved for this machine; opening the picker")

    dialog = CameraSelectDialog(current_index=saved)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        return dialog.selected_index
    return saved


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    app = QApplication(sys.argv[:1])
    # Kept in step with config.MachineSettings, which names the same pair
    # explicitly. QSettings keys off these two strings, so a mismatch would
    # quietly write preferences somewhere nothing reads them.
    app.setOrganizationName(machine_settings.ORGANIZATION)
    app.setApplicationName(machine_settings.APPLICATION)

    # Applied to the QApplication rather than to each window, so every widget
    # and dialog created after this point is themed without having to ask.
    if not theme.apply_theme(app):
        logger.warning("Running with Qt's default appearance; style.qss was not found")

    config.ensure_storage_dirs()
    logger.info("Configuration:\n%s", config.describe())

    # Before anything that could fail obscurely. In a frozen build a missing
    # .env, an absent model pack or a stopped MySQL each produce a window that
    # appears and vanishes, and PLAN.md's Phase 11 Definition of Done asks for a
    # helpful dialog rather than a stack trace. See app/ui/first_run.py.
    if not args.skip_checks and not first_run.run_checks():
        logger.info("Start-up checks were not satisfied; exiting.")
        return 1

    index = resolve_camera_index(args)

    window = KioskWindow(camera_index=index)
    if machine_settings.fullscreen and not args.windowed:
        window.showFullScreen()
    else:
        window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

