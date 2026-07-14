"""
validation/reference_runner.py

Step 8 of the assignment requires running the course's reference code(s) at
least once and comparing results. No reference implementation was supplied
alongside Project.txt / the HTML dashboard in this session, so this module
is a clean *hook*: point REFERENCE_SCRIPT_PATH at the instructor-provided
script and `run_reference()` will execute it and capture its stdout/return
value for `result_comparator` to diff against our own KPIs.

Until a reference script is supplied, `validation.result_comparator` falls
back to a brute-force enumeration of all C(7,3)=35 possible charging-station
placements (see main.py) as an internal correctness baseline: since the
search space is small enough to enumerate exhaustively, this gives a true
optimum to check the GA against even without external reference code.
"""
import subprocess
import sys
from pathlib import Path

REFERENCE_SCRIPT_PATH = None  # e.g. Path("/mnt/user-data/uploads/reference_solution.py")


def run_reference(script_path=None, args=None):
    script_path = script_path or REFERENCE_SCRIPT_PATH
    if script_path is None or not Path(script_path).exists():
        return {
            "ran": False,
            "reason": "No reference script supplied/found. Set "
                      "validation.reference_runner.REFERENCE_SCRIPT_PATH "
                      "to the course-provided file and re-run.",
        }
    cmd = [sys.executable, str(script_path)] + (args or [])
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    return {
        "ran": True,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }
