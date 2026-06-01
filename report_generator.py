"""
report_generator.py
-------------------
Generates a polished .docx report from analysis results.
Calls the Node.js _make_report.mjs script via subprocess.
"""

import datetime
import json
import logging
import os
import subprocess
import tempfile

logger = logging.getLogger(__name__)

_NODE_SCRIPT = os.path.join(os.path.dirname(__file__), "_make_report.mjs")


def generate_report(results: list[dict], output_path: str = None) -> str:
    """
    Write analysis results to a Word .docx file.

    Args:
        results:     List of per-ticker result dicts from main.py
        output_path: Optional explicit output path; auto-generated if None.

    Returns:
        Absolute path to the generated .docx file.
    """
    if output_path is None:
        date_str = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        output_path = os.path.join(
            os.path.dirname(__file__),
            f"stock_analysis_{date_str}.docx",
        )

    if not os.path.exists(_NODE_SCRIPT):
        raise FileNotFoundError(
            f"Node script not found: {_NODE_SCRIPT}\n"
            "Make sure _make_report.mjs is in the same directory."
        )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump(results, f, indent=2)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            ["node", _NODE_SCRIPT, tmp_path, output_path],
            capture_output=True,
            text=True,
            check=True,
        )
        if proc.stdout:
            logger.info(proc.stdout.strip())
    except subprocess.CalledProcessError as exc:
        logger.error("Report generation failed:\n%s", exc.stderr)
        raise
    except FileNotFoundError:
        raise RuntimeError(
            "Node.js is not installed or not in PATH. "
            "Install it from https://nodejs.org and run: npm install docx"
        )
    finally:
        os.unlink(tmp_path)

    return os.path.abspath(output_path)
