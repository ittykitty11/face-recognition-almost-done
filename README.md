# CSU Attendance Monitoring System

A face-recognition attendance kiosk for Cagayan State University. An employee
stands in front of a camera, the system recognises them and writes the time —
first scan of the day is a time-in, a later scan is a time-out. Everything runs
on one Windows machine: a PySide6 desktop application, InsightFace for
recognition, and a local MySQL/MariaDB database. There is no web server, no
cloud service, and no data leaves the institution.

---

## What it looks like in use

The kiosk screen is designed to be read from one to two metres away, by someone
who is walking, in about two seconds. Punch confirmations appear below the
camera while the monthly PDF stays visible beside it; problems use a full-screen
message:

| Screen | Meaning |
|---|---|
| **Green**, with a name | Recognised — time recorded |
| **Blue**, with a name | Already recorded a moment ago; no second record made |
| **Red**, "Not recognised" | No enrolled face matched |
| **Red**, "Live person required" | A photo or a screen was held up (anti-spoofing) |
| **Amber**, "One person at a time" | Several faces in view — the system refuses to guess |
| **"Step closer"** | No face detected |
| **Red**, "System problem" | The database is unavailable; the time was *not* recorded |

A strip along the bottom shows the last five people recorded, so somebody
walking away can confirm their scan registered.

When an employee clocks in or out, the live camera stays visible beside that
employee's monthly Form 48 PDF. The kiosk updates the same 31-day time and
hours table used by the exported PDF. Use the employee search above the PDF to
view another employee's current-month record; the panel also states whether
attendance was recorded for that employee today.

---

## Requirements

| | |
|---|---|
| **Operating system** | Windows 10 or 11, 64-bit |
| **Python** | **3.13, 64-bit** — `requirements.txt` pins `onnxruntime==1.28.0` and `PySide6==6.11.1`, which ship wheels for cp313/win_amd64. Other versions will try to build from source. |
| **Database** | MySQL or MariaDB. XAMPP is the easiest — it bundles MariaDB and phpMyAdmin. |
| **Camera** | Any built-in or USB webcam. A phone can be used instead via [Iriun Webcam](https://iriun.com/) (desktop client + phone app). |
| **Disk** | About 1 GB free. The face-recognition model pack is ~300 MB and downloads on first run. |
| **Internet** | Needed for `pip install` and for the first run only. After that the system is fully offline. |

---

## Installing on another computer

### 1. Install Python 3.13

Download from [python.org](https://www.python.org/downloads/), 64-bit installer.
**Tick "Add python.exe to PATH"** on the first screen.

Check it:

```
python --version
```

### 2. Install XAMPP

Download from [apachefriends.org](https://www.apachefriends.org/). You only need
the **MySQL** component; Apache and the rest can be left unticked.

### 3. Get the code

```
git clone https://github.com/mranz/Face-Recognition-AMS.git
cd Face-Recognition-AMS
```

Or download the ZIP from the repository page and extract it.

### 4. Create the virtual environment and install the dependencies

```
python -m venv .venv
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

This takes a few minutes — PySide6 alone is a large download.

### 5. Create the configuration file

```
copy .env.example .env
```

Open `.env` in Notepad and set at least these two:

```
DB_PASSWORD=            # the MySQL password; blank is correct for a stock XAMPP
ADMIN_PASSWORD=123 # CHANGE THIS -- it gates every administrative action
```

`.env` is deliberately not in the repository. It holds the database and
administrator passwords, and a password committed to a repository is not a
password.

### 6. Start the database

Open the **XAMPP Control Panel** and press **Start** on the **MySQL** row.

> MySQL is **not** installed as a Windows service by XAMPP, so it does not come
> back automatically after a reboot. It has to be started before the application
> each time, or nothing can be recorded.

### 7. Create the database schema

```
.venv\Scripts\python.exe scripts\init_db.py
```

This creates the database, the five tables, and the default settings. It is safe
to run again at any time — it never overwrites a setting you have changed.

### 8. Run it

```
.venv\Scripts\python.exe main.py --windowed
```

> **The first launch downloads about 300 MB** — the InsightFace `buffalo_l`
> model pack, into `models/buffalo_l/`. This happens once, and there is no
> progress bar for it, so the first start can look like it has hung for several
> minutes. Let it finish. Every launch after that reaches recognition-ready in
> about **3 seconds**.

You should see live video within a second or two. The screen says
*"Starting up — loading face recognition"* until the models are loaded.

Drop `--windowed` to start fullscreen, which is how it should run in production.

---

## First-time setup: enrolling someone

Nobody is enrolled yet, so at this point every face gets **"Not recognised"**.
That is correct behaviour, not a fault.

1. Click **Administration** at the bottom of the kiosk screen
2. Enter the administrator password (from `.env`; `123` unless you changed it)
3. **Employees** tab → **Add employee** — fill in the number, name and department
4. **Tick "Consent"** and set the date consent was given

   > Enrollment is **refused** without a consent date. Face data is sensitive
   > personal information under RA 10173, and consent is what makes processing
   > it lawful. This is not a setting that can be turned off.

5. Select the employee → **Enrol / re-enrol face** → **Start**
6. Follow the five on-screen poses: look straight, turn slightly left, slightly
   right, chin up, normal expression. Three seconds between shots.
7. Close the admin window

Stand in front of the camera and you should see your name within a second or two.

**Enrol at the kiosk, in the kiosk's lighting.** An enrollment done in a bright
office for a kiosk in a dim corridor produces someone the system struggles with
every morning.

---

## Command-line options

```
.venv\Scripts\python.exe main.py [options]
```

| Option | What it does |
|---|---|
| `--windowed` | Start windowed instead of fullscreen. Use this while developing. |
| `--camera 1` | Force a camera index for this run only; does not change the saved choice. |
| `--select-camera` | Open the camera picker at startup even if one is already saved. |
| `--log-level DEBUG` | More detail in the console. Default is `INFO`. |
| `--skip-checks` | Skip the start-up configuration, model and database checks. |

The chosen camera index is stored per machine (in the Windows registry, via
`QSettings`), because Windows enumeration order differs between computers.

---

## Running the tests

```
.venv\Scripts\python.exe -m pytest tests\ -q
```

489 tests. Those that need a database skip themselves automatically when MySQL
is not running, so the suite passes either way — you will simply see fewer tests
run.

> **Run the application once before running the full suite.** Some tests build a
> real kiosk window, which starts the recognition worker, which begins
> downloading the model pack if it is not there yet. On a fresh clone that
> download gets interrupted when the test finishes and takes the test process
> down with it. Either launch `main.py` once and let the download complete, or
> skip those tests until you have:
>
> ```
> .venv\Scripts\python.exe -m pytest tests\ -q -m "not gui"
> ```
>
> That runs 391 tests and needs neither the model pack nor a camera.

---

## Optional extras

### Anti-spoofing

With `liveness_enabled`, the kiosk requires one randomized head turn, then
checks the face with the passive anti-spoof model before matching.
The anti-spoof model is warmed during startup so its first inference does not
slow down an employee's scan. The challenge allows up to eight seconds; a
timeout or a brief loss of face landmarks asks the person to retry rather than
labeling the scan as a spoof. This adds protection against still photos and
replay attempts, but is not a guarantee against video replay. Test live people
and attack examples on the deployed camera before relying on it. See
[`models/anti_spoof/README.md`](models/anti_spoof/README.md) for what to install
and how to turn it on.

### Building a standalone .exe

To run on a machine that has never had Python installed:

```
build.bat
```

Produces `dist\CSU Attendance\` (about 750 MB, most of it the model pack). Copy
that whole folder to the target machine, create a `.env` beside the `.exe`, and
run it. The model pack sits *beside* the executable rather than inside it, so
start-up stays fast.

### Scheduled maintenance

Two jobs should run nightly in a real deployment. Each prints its own scheduled
task command with this machine's paths already filled in:

```
.venv\Scripts\python.exe scripts\backup_db.py --show-task
.venv\Scripts\python.exe scripts\purge_captures.py --show-task
```

- **`backup_db.py`** — nightly `mysqldump`, gzipped, keeping the newest 60. Every
  dump is verified, because a truncated backup otherwise looks fine until the day
  it is needed.
- **`purge_captures.py`** — deletes face images older than the retention period.
  This is the promise the privacy notice makes. A dry run is the default; pass
  `--apply` to actually delete.

### Measuring the recognition threshold

The similarity threshold should be set from measurement, not guesswork:

```
.venv\Scripts\python.exe scripts\calibrate_threshold.py storage\eval\test_set
```

Give it a folder of images named `{employee_no}_{n}.jpg`. It computes false
acceptance and false rejection rates across a range of thresholds, reports the
equal error rate, writes CSVs and plots, and recommends an operating point.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| "Cannot reach the database" | MySQL not started | XAMPP Control Panel → **Start** on MySQL |
| The first launch seems frozen | Downloading the ~300 MB model pack | Wait. It happens once. Check `models\buffalo_l\` is growing. |
| "No working camera found" | Camera in use by another program, or Iriun not running | Close Teams/Zoom, start the Iriun client, then **Rescan** |
| Everybody gets "Not recognised" | Nobody is enrolled yet | Enrol somebody — see above |
| One person is never recognised | Enrollment lighting differed from the kiosk's | Re-enrol them at the kiosk |
| `ModuleNotFoundError` on launch | Running the system Python, not the venv | Use `.venv\Scripts\python.exe`, not `python` |
| Install fails building a wheel | Not Python 3.13 64-bit | Check `python --version` and the architecture |
| Preview lags behind reality | Phone on a weak WiFi link | Connect the phone by USB |

---

## Project layout

```
main.py                  entry point and start-up sequencing
app/
  config.py              environment, paths, per-machine settings
  database.py            SQLAlchemy engine and per-thread sessions
  models.py              the five tables, and the embedding codec
  face_engine.py         InsightFace wrapper
  matcher.py             in-memory embedding index
  attendance.py          time-in / time-out rules
  employees.py           employee records and the consent gate
  enrollment.py          averaging, consistency checks, storage
  reports.py             report queries and CSV/Excel export
  liveness.py            passive anti-spoofing
  calibration.py         FAR/FRR/EER analysis
  retention.py           capture deletion
  workers/               camera, recognition, database, enrollment threads
  ui/                    kiosk, enrollment and admin windows
scripts/                 setup, diagnostics, evaluation, maintenance
tests/                   489 tests
docs/                    user manual and privacy documentation
```

Business rules live in plain Python functions with no Qt in them, so they can be
tested and read without a screen. Nothing that takes longer than about 100 ms
runs on the GUI thread.

---

## Documentation

- **[docs/PROJECT_GUIDE.md](docs/PROJECT_GUIDE.md)** — explains the project
  folders, source files, scripts, models, storage, tests, and how they work
  together.
- **[docs/MAIN_PY_EXPLAINED.md](docs/MAIN_PY_EXPLAINED.md)** — a detailed
  walkthrough of the application entry point.
- **[docs/USER_MANUAL.md](docs/USER_MANUAL.md)** — for HR staff and
  administrators. Daily operation, enrolling people, corrections, reports.
- **[docs/PRIVACY.md](docs/PRIVACY.md)** — for the Data Protection Officer. What
  personal data is processed, why, for how long, and what in the code enforces
  each claim. Includes draft text for the employee privacy notice.

---

## A note on privacy

This system processes biometric data, which is sensitive personal information
under Republic Act 10173. Before deploying it:

- Change `ADMIN_PASSWORD` from `123` — the application warns on screen
  until you do
- Obtain and file written consent from every employee before enrolling them
- Set up the capture retention job, so the deletion promise in the privacy
  notice is actually kept
- Have the Data Protection Officer review `docs/PRIVACY.md`
