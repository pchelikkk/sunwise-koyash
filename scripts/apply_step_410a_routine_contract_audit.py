#!/usr/bin/env python3
r"""Apply KOYASH Step 4.10A routine quality contract and audit.

Run from the repository root:
    py -3.12 .\scripts\apply_step_410a_routine_contract_audit.py

The script is idempotent, writes only Step 4.10A files, and refuses
to run on the wrong branch or on an incomplete Step 4.9C base.
"""

from __future__ import annotations

import base64
import compileall
import subprocess
import sys
import zlib
from pathlib import Path

EXPECTED_BRANCH = "step-4-10a-routine-contract-audit"
SCRIPT_PATH = "scripts/apply_step_410a_routine_contract_audit.py"
TARGET_PATHS = {
    'backend/app/algorithms/routine_quality.py',
    'backend/app/algorithms/routine_quality_scenarios.py',
    'backend/scripts/audit_routine_quality.py',
    'backend/tests/test_routine_quality_contract.py',
    'docs/routine-quality-contract.md',
    'docs/routine-quality-audit.md',
    'docs/routine-quality-baseline.json',
}
ALLOWED_DIRTY_PATHS = TARGET_PATHS | {SCRIPT_PATH}

FILES_B64: dict[str, str] = {
    'backend/app/algorithms/routine_quality.py': (
        'eNrVHGtz28bxO3/FFV8C2BAjN4/OcEJP1UTueJpIriSn09FwMBBxlDAGARoHyGZU/vfu3gt3hwNIJVLT+INNHG537/a9ewev6mpN'
        'kmTVNm1Nk4Tk601VNyQty6pJm7wq2WSywjnLqijoko+oSd9XbdnQWrzP0iZdFiljVL9PWZYvm7h7JWY2201e3qpJJ+U2Jj/mgCct'
        'JKl0s5mmxW1V583dmk1XeQFvO6ybTbFN7tI6S+QbL1RZ1eu0yH+htV7u+dn3pxdnycmPb08uTy9joqdkSU0/tpQ1Xkx11TZ5SZOb'
        'Ni+yDh1/TORLLyBbwq9up5fwSLN3dZW1yBV8S5ONePTvgQGYgQAfEw6WeeBwfErLdm3Ip1zSuozJhVjkZUM33Xy2vKPrFLZHl9V6'
        'TcuMi1vBXlijF5I9kx9O/v3u5OLqksxJGKyruoTlBTEJ6D3lP6PJP87O/3WWXJy/v3p7dppcXp2+45MnBP4Ey4KmJaN1EIvnpiq7'
        'Bxhv1/pNTdMG6DdqYF3lDHQUBaoBNiv1k35eVUXO16oBUvYBfkeTn84vzt6e/T05v/jh9ALW8uCsZUZeHVvrmZE/H1trmpGvjnvr'
        'mpGvjz1rm5Fvjo31zci38LibnP58eugizL0YS1Fr+8pd29e+tX3jX9u3xyZ3ZuQvfHE/nL45ef/jVXL+8+nF+8vT5OLk6u05LPJ4'
        '+u1kcgmyBX3cwrM00+uA1nVVo9xv0w3+8ykVmrCYTCZ/1eYegq79Qsv5Vd3SaMKHyD9bsLhm+yYvMwCY8cUsq4zOCGtq/sQkvRlR'
        'lPnwmjKW3hrzsnS7SeuGD5D/kDNgDywR/+GvldUyUPqhOdKIEvoZ9lWmRZJnQ1OXKSwYdkaT9D7Ni/SmgKXcVFXhzBVLoyuyhk0V'
        'SdauNyGjxSoiR68JusNrwB+j11uIzfO1UpBQSR4+UNj1fVq0lKyqmsBjLB/zUnpTgWwKglizMCL5Sk1g4M4avoYdCAFXoHxEgiaf'
        'IESIf82Q+OByAGHO8pI1KfgOPj+2HVfUWzZOmkpak0EkSMyALcGd0Ay4xqFvaRMGEgX4EDXJxiNAepiMlYgZvvVNTHkDVSCYNk0t'
        '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'
    ),
    'backend/app/algorithms/routine_quality_scenarios.py': (
        'eNrNl09v2jAYxu98CivnXMaqaaq0A+t6QJpAK+1hQsgy8Uuw5tiZ46BF07773jiBhCS1oKMdHAoFP28e++fHfzZGJ8QWqVAxEUmq'
        'jSUTVYxGD/Onx+nsnn57mnydPn6ni7v72eRhOl/cEikyu+QissvMmrBsvlqRT2Q5Ivj67f6Wr0Dw4JYEkU7WQjErtKIsUkAzWOcJ'
        'VZpuDIsNUxEEYSOywkoodXeNjmQ/hApJqSZMceIqhERpMlhCqDS3WKKx4r5mcVl3fBMef13WpjgA0DEbdNpFGh9jVIbNlkFpJQhR'
        'XDoJVp2m65zHUDoI1kyW7ni3GPyKZM6BUxx2A1yAslXhpkPdolGeWZ1QAzjoOPbo0ClWvcopGKwXuf7EueD9p++YzKF6Xoq1gP7M'
        'mRS2aD/zT/WxfutRzUBlwoodoCGGbnYoP2JKmYz0VstBtou92pF1TJsyx2CJNmSglJ/xRx/jg3Uv4cbP6+DFybPv1tuQxqm9wXS7'
        'Was3luI/SS7ZGcy5KSiHbcFNleZEKJFglOvxGAL9xRSO7l4GvM5yrSV9rZfs+3c+smjQyxR/V5Bl5RC0+uHhW7s8Fe91R1YLWbRX'
        '4BPwzVHyzOL7QoBjL8DS4kXW3esF59zjRitx5dS5FQrOQKgws0zSVMQJWq9SyHMpq1k9AHDmBDXCtqxK5YDUHz/v5lm58/JrW3Ax'
        '3Du43Br7NizPj98aYqEUGFrTx80SO46uBRLFiT8M8HOtIpWK1HPG7ZEHOenK/REcX+IE1FpLX2er7AzORbDuGXjAdrIZksPGeTrq'
        'hNnc4AkoBhptmYoho6mBRBwtSA3jSQykblfFshpaDGwlOneNvRn/Y0pbxl1Ia9TPw+337ooi+iKE7VsLXoqQIObVd6TtX1ecrHNf'
        'Ofsk++ESWXVOXuW68t+OsCccglajv+bqC/k='
    ),
    'backend/scripts/audit_routine_quality.py': (
        'eNqdVVFv2zYQfvevOPCl8marQ54GAypgFBmWbUi6ON1QpAHBiJTNRSI1kqptFP3vO4qkJdsJ0MxP5h3v7uN9351k02rjgJl1y4wV'
        'ExnO/1itJpXRDbTMbWr5CNHxAY/B4fatVOtkX6r9JNhZ2+asXmsj3aaxudGdk0rQfztWS7dP9x87WXPKOi4dNcKbviea2lIoZqS2'
        'Kc/tzce7q+tL+ufH5R9Xd5/o6v3l9fL26mY1pAs3hbF5azTvSkc5c8wKl3LUmnEafZb6uHRjMplwUUHfGoo9stkU5u8O3cqvWSNs'
        'y0qxmAD+eqOBYriwNOuuEcp96D1Zf8v/uLClka2TWhVk6bsAv998Wq5+hfhiSP1iayaVdeA2AoxgNUSgECHmZNZnnY4Q5IxzD7cv'
        'PRQl83kMijEBScW62hXkrfe9TW3Id7Xdja5tRN0WxLMPTsPRLdAG3q/++n+A8LVt584K/Y38i/7NXCB1jVTSOlnCb6ubawh68Tjc'
        'Rtpeoa8rWjFZz7Wal1o5w0o3F8ZoY0co0NhTY502gjrTiTOIlzskbYsyhVJzARew3QgFTKHE1Rfkjh+oTGUAwfrnlE7w1wEudYMq'
        'c68E2CDAGBka54UkGAdd4V+ORQTvHcdgjHCdUQnTWPtxHKjfDtSJncsCFQvgsnT31pmZXwQPM/hhliov4FHruh8b9Ic5kdXBe8Ac'
        'q/rUOe+a1sbcMxDKdvhGZkspi19YbcUMLHrok9jb4g6ffoT7OzOEBhQX57nCIxscuzDtUkWYvgk43Ecd6dkz4osUW3S9vEkyPzqZ'
        'D8qjZZpQ92IuntmIgwRSyiKWSpvMDpwfNmPx4kocDX2AQHvd01J32IlaqCylD/MwHavC040oz7g/EF30j4sH7GIkureGKR/IDmfq'
        'JxdzDq0J9ulz97wQkbC8eeLSZOEQGEN+d7gdqH4aieE0eusXSsDdv+RHIJ8V8dLA6cXvWEE6V81/RosS2xqntvD+6YgBlEFWkduT'
        '9Rzp8+kdjr/TC/g6qvstphCoucVJMo8j9sl2TcPMHnsR8t2TaCEPkyFg2AinKOLtBZDDnYoMivga/fdvki1w/ubh2+woJG2qIIxx'
        '4LHnhfD0lV6zdhw7Mh8CSZTWkUz8XqYorxMYuFR5euI9eQ4JeThbJBfjnfATDjUWoVThB5tSKAoglPoRp5SEUMOkFbDa44Zs/GrP'
        'wgKYTv4DSBn7sg=='
    ),
    'backend/tests/test_routine_quality_contract.py': (
        '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'
        'HceDroqgQ+fE9v4F5NF//Q=='
    ),
    'docs/routine-quality-contract.md': (
        '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'
        'VU6k/977spsxXlizqE4u0mM0i/hvD08E+g=='
    ),
    'docs/routine-quality-audit.md': (
        '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'
        'Z+2IDreUtdJNIf4H0g9cdQ=='
    ),
    'docs/routine-quality-baseline.json': (
        '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'
    ),
}


def _run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result.stdout


def _dirty_paths() -> set[str]:
    result: set[str] = set()
    for line in _run_git("status", "--porcelain=v1", "--untracked-files=all").splitlines():
        if len(line) < 4:
            continue
        path = line[3:].strip().strip('"')
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result.add(path.replace("\\", "/"))
    return result


def _require_repository_root(root: Path) -> None:
    required = [
        root / ".git",
        root / "backend/app/algorithms/routine_builder.py",
        root / "backend/app/importers/product_dataset.py",
        root / "data/products.xlsx",
        root / ".gitlab-ci.yml",
    ]
    missing = [str(path.relative_to(root)) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "Run this script from the KOYASH repository root. Missing: "
            + ", ".join(missing)
        )


def _require_branch() -> None:
    branch = _run_git("branch", "--show-current").strip()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, current branch is {branch!r}."
        )


def _require_clean_scope() -> None:
    unexpected = sorted(_dirty_paths() - ALLOWED_DIRTY_PATHS)
    if unexpected:
        raise RuntimeError(
            "Refusing to overwrite a working tree with unrelated changes: "
            + ", ".join(unexpected)
        )


def _require_step_49c_base(root: Path) -> None:
    ci_text = (root / ".gitlab-ci.yml").read_text(encoding="utf-8-sig")
    if "pytest -q" not in ci_text:
        raise RuntimeError(
            "Step 4.9C CI coverage is missing: .gitlab-ci.yml must run pytest -q."
        )

    dashboard_path = root / "backend/app/api/v1/endpoints/admin_analytics.py"
    dashboard_text = dashboard_path.read_text(encoding="utf-8-sig")
    if "/dashboard" not in dashboard_text or "AnalyticsDashboardResponse" not in dashboard_text:
        raise RuntimeError(
            "Step 4.9C protected analytics dashboard is not present in this branch."
        )


def _decode(payload: str) -> str:
    return zlib.decompress(base64.b64decode(payload)).decode("utf-8")


def _write_file(root: Path, relative_path: str, content: str) -> str:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists() and path.read_text(encoding="utf-8-sig") == content:
        print(f"unchanged {relative_path}")
        return "unchanged"

    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"written   {relative_path}")
    return "written"


def _validate_python_files(root: Path) -> None:
    python_paths = sorted(path for path in TARGET_PATHS if path.endswith(".py"))
    for relative_path in python_paths:
        path = root / relative_path
        if not compileall.compile_file(path, quiet=1, force=True):
            raise RuntimeError(f"Python compilation failed: {relative_path}")

        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if len(line) > 100:
                raise RuntimeError(
                    f"Line exceeds 100 characters: {relative_path}:{line_number}"
                )


def main() -> int:
    root = Path.cwd()
    _require_repository_root(root)
    _require_branch()
    _require_clean_scope()
    _require_step_49c_base(root)

    print("Applying Step 4.10A routine quality contract and audit...")
    states = [
        _write_file(root, relative_path, _decode(FILES_B64[relative_path]))
        for relative_path in sorted(FILES_B64)
    ]
    _validate_python_files(root)

    written = states.count("written")
    unchanged = states.count("unchanged")
    print()
    print("STEP 4.10A APPLIED")
    print("- deterministic routine contract with error/gap/warning findings")
    print("- candidate-aware missing-step diagnostics")
    print("- eight fixed customer scenarios over data/products.xlsx")
    print("- dataset step coverage, product reuse, and terminology drift audit")
    print("- tracked deterministic baseline and regression snapshot")
    print("- no recommendation, filter, scoring, or builder behavior changed")
    print(f"- files written: {written}; unchanged: {unchanged}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
