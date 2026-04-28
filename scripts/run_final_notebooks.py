from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"

NOTEBOOK_ORDER = [
    "00_Master_Pipeline.ipynb",
    "01_Data_and_Statistical_Tests.ipynb",
    "02_Strategy_and_WalkForward.ipynb",
    "03_Performance_Metrics_Extended.ipynb",
    "04_Two_Market_Diagnostics_Story.ipynb",
    "05_Two_Market_Trend_Following_Story.ipynb",
    "06_CPP_Confirmed_Story.ipynb",
]

PROFILES = {
    "all": NOTEBOOK_ORDER,
    "story": [
        "04_Two_Market_Diagnostics_Story.ipynb",
        "05_Two_Market_Trend_Following_Story.ipynb",
        "06_CPP_Confirmed_Story.ipynb",
    ],
    "confirmed": [
        "04_Two_Market_Diagnostics_Story.ipynb",
        "06_CPP_Confirmed_Story.ipynb",
    ],
    "cpp_only": [
        "06_CPP_Confirmed_Story.ipynb",
    ],
}


def run_command(args: list[str], cwd: Path) -> None:
    print(f"[run] {' '.join(args)}")
    subprocess.run(args, cwd=str(cwd), check=True)


def execute_notebook(path: Path, timeout: int) -> None:
    print(f"[notebook] executing {path.name}")
    notebook = nbformat.read(path, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(path.parent)}},
    )
    client.execute()
    nbformat.write(notebook, path)
    print(f"[notebook] wrote {path}")


def refresh_confirmed_artifacts(refresh_diagnostics: bool, refresh_cpp_story: bool) -> None:
    if refresh_diagnostics:
        run_command(
            [
                sys.executable,
                str(ROOT / "scripts" / "export_diagnostics_story.py"),
                "--skip-notebook",
                "--output-dir",
                "results_diagnostics_story",
            ],
            cwd=ROOT,
        )
    if refresh_cpp_story:
        run_command(
            [
                sys.executable,
                str(ROOT / "scripts" / "build_cpp_story_notebook.py"),
                "--execute",
            ],
            cwd=ROOT,
        )


def resolve_notebooks(profile: str, only: list[str] | None) -> list[Path]:
    names = PROFILES[profile]
    if only:
        only_set = set(only)
        names = [name for name in names if name in only_set]
    paths = [NOTEBOOK_DIR / name for name in names]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing notebooks:\n" + "\n".join(missing))
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh and execute final project notebooks.")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        default="confirmed",
        help="Notebook set to run. Default keeps the refresh focused on confirmed story notebooks.",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        help="Optional explicit notebook filenames to restrict within the chosen profile.",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=1800,
        help="Per-notebook execution timeout in seconds.",
    )
    parser.add_argument(
        "--skip-diagnostics-refresh",
        action="store_true",
        help="Skip rebuilding results_diagnostics_story before notebook execution.",
    )
    parser.add_argument(
        "--skip-cpp-story-refresh",
        action="store_true",
        help="Skip rebuilding 06_CPP_Confirmed_Story.ipynb from confirmed outputs.",
    )
    args = parser.parse_args()

    refresh_confirmed_artifacts(
        refresh_diagnostics=not args.skip_diagnostics_refresh,
        refresh_cpp_story=not args.skip_cpp_story_refresh and ("06_CPP_Confirmed_Story.ipynb" in PROFILES[args.profile]),
    )

    notebook_paths = resolve_notebooks(args.profile, args.only)
    for path in notebook_paths:
        if path.name == "06_CPP_Confirmed_Story.ipynb" and not args.skip_cpp_story_refresh:
            # Already rebuilt and executed by the generator above.
            print(f"[notebook] skipping direct execution for {path.name}; refreshed via build_cpp_story_notebook.py")
            continue
        execute_notebook(path, timeout=args.timeout)


if __name__ == "__main__":
    main()
