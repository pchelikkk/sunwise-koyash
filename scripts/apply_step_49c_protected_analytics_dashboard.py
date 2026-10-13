#!/usr/bin/env python3
r"""Apply KOYASH Step 4.9C protected aggregate analytics dashboard.

Run from the repository root:
    py -3.12 .\scripts\apply_step_49c_protected_analytics_dashboard.py

The script is idempotent and refuses to run on the wrong branch or on an
unfinished Step 4.9B1 base.
"""

from __future__ import annotations

import base64
import subprocess
import sys
import zlib
from pathlib import Path


EXPECTED_BRANCH = "step-4-9c-protected-analytics-dashboard"
SCRIPT_PATH = "scripts/apply_step_49c_protected_analytics_dashboard.py"
ALLOWED_DIRTY_PATHS = {
    SCRIPT_PATH,
    "backend/app/schemas/analytics.py",
    "backend/app/repositories/analytics_repository.py",
    "backend/app/services/analytics_service.py",
    "backend/app/api/v1/endpoints/admin_analytics.py",
    "backend/tests/test_analytics_dashboard.py",
    "docs/analytics-dashboard.md",
    "docs/admin-security.md",
    "docs/analytics-event-contract.md",
}

FILES_B64: dict[str, str] = {
    'backend/app/schemas/analytics.py': (
        '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'
        '+Nk='
    ),
    'backend/app/repositories/analytics_repository.py': (
        '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'
    ),
    'backend/app/services/analytics_service.py': (
        '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'
        '3ss+PHCrvbPT8ZCGmX08N9f+A/NprUs='
    ),
    'backend/app/api/v1/endpoints/admin_analytics.py': (
        'eNrNV1tv2zYUftev4PwkbYratOseAiiYl3hbgDRLnaRYEAQELdEOAYnUKMqJs+2/7/AiURe33dZhmx9smefCcz+f'
        'WFkJqVAhNhvGN8FaihLlRFHFSoqYJd5cn8TdYYz8d04LRayM2lUg30rMORcKBPIYHneBZVmTWpGKdTyXZ0vRKCpj'
        'dEoryvM6Rj9eX18unjJaKSZ4jN41VO5iBGKqqa2SalcKvhEJqXc8e5CCi6ZOwDayInVn8FwTT92hu51UVQK3J9vD'
        'JDfXUZ4xWrcikv7SMEkxyUvGvUQmJIUvvmadbxuqcE2VAnfrEWM/aI3KMBePniNfJcb0fNXX1Jru+SStRM2UkGBd'
        'QjgpdoplNe6Odz7IjrbsSF5LnT3QkvQUTKROSf2wEkTmS1pXgtc09rSrpiyJ3LWUnloqtywbGOaOJvqv7HkQSJNl'
        'lPqMh5Wka/aUzl6YcL/olM2grsimTu9mhoA84T4KdI0aPa5YE4jfuTkLMeakpBhHQRC8nf+M390slrd4Ob/4YYFP'
        '57dXIPT6mzdAzOnahH1ifhgg+LTZOPIVfDcopjso5/uuYMN+BqP7OIjQwfEkAkdGtaSqkXxCtPfqz75Up3tyHHYX'
        'xkY2cm5hUmMounBLigYcaPvVmNT+saawNTJMiXpmfC0Qq9GF4I7Ys9UygTUFAUMtcwrDIAomTNDaoP4ZtISGwZkk'
        'aS2KLYUYuVrDFZVM5NbrL2MX9F19hBhX7V9FsS447wP6zRjYoyuxh2pcVU1V0Ds/rdqn+y4NlOvpgvW1UBclefI5'
        'OIy7Ryi/sN/qYdRvRvKI6RYUYaUKoylG++quS5ELe9g51wY9Ql+k7lh1mYh6qSAM5tpgLnpz9ccOR5yJnKb2OdHc'
        '+OtXr/DNxeXyp5PF1dX8u/MFXlxcn13fxgPpnCrCinTm7SI8b0OMyqZWaEVRJcWW5TRHSkBIHqiceS2Qa+fcwDfo'
        'HuPKQF/v3HvIhSxJwZ5pboXTrpI7hdE+ZtA3YlXCGeMMGms+TofyR4NQfDLSnx/t/RFvo0yJLBgMOPVAeBuy2VDB'
        'B/2DYBxM/fVLOtQ1mg6LP/ov/Z+q1p+ZX1c6AGAT31CUET2MEQWzoAah95DpPd/LR2i2V9169uvQ5d/NsJkyRx8M'
        's5tyo9DGw9j3WgBmyvFoyPzbzTwN7T8Y1j8V0mgyHpQALgwuAUJIu5kMqKlcMdgZDizBjNWkMLLwMoEZDE/79473'
        'sq/7YFzyJiMH6LBnUp//qzH/YW+rfmuRi8YZ9rbZi26RucaUDiHhElJWpB8BV7ZEeFY0OcWMYwvQ0u9JoYlRYAAt'
        '0lvTr5nuNns9zhop9dIx4KiPUXKWKY9KBlhWwxJTWg6M9JHNCIsMcc0EIrWa7L72avTmtlAd5NLDGBU0BbQV3WvU'
        '9XKy1HtWjxa4U2IE9+z7vyI4BGKTbLRYwKCTtqW7v3azfBy7tIEwBRb3jpyfafc0IiqRut8+NlByN4Ff5JEw1eYt'
        'GdXC9MKhN1MmuLjnYb9D9Tc1Awl1cwmRWp95oyz6Tmg3uGYnoilys9BXDYOnEWRHvleiz5+Ab16+xleL5fuzkwVM'
        'wvn7+dm5noP70cx8aoPGHorqVxQiWbFDDSdb4CWrgvbBDDKLE5zc3/61fS/6RPOP3p7+Vuu7m/43jT96sxl6OHjD'
        'GZZt60cU/AHShkaf'
    ),
    'backend/tests/test_analytics_dashboard.py': (
        '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'
    ),
    'docs/analytics-dashboard.md': (
        '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'
    ),
    'docs/admin-security.md': (
        'eNq9VMtuHDcQvM9XNKDrPmzEJ+kSGQpixTAsQDKCnDQ9ZO8uvXyZ5Oxq/j5FzngtI0COvg2ni/2oquYVffz8z+3j'
        'B2LtjKcsakymTDSE0WtOU9c9HWQJsmc7FaMy3T7ck8lkfBFfTMB/O5EPhfIhnD3+0+coHqjt45n3e0m4q+uNirHG'
        'H0XTLgVHBcl9SI4tjRmwmjHtWMmm626VkpwpjVbyddetAaRBOAFWwlH8NfXv3rztbxBhVcxJ5hRnUw6UghXq67lv'
        'sN/+D9amAw5ThLPoijT+FRY9iGMMNdigjjMgyd7kkrhO34aLKewMso1RcxHEv4oqbb6+VulpZ8S2q3/9/US5hCSZ'
        'ggdvFTMPr1d0PtQk9ReESGB37hHU2cD6O22fgt+Hu/e4T3KSNKHct1FyWVEOpMWF1lbhI2rIblc7Mc6JNmjNTptZ'
        '1DgO1qhXqorXMUAB8KQklqU9ZQ3aWGfeCX25r/WAKFOUvKFHSSi/huborEUy5VEdiDPtRPTA6rj6L1dJooXGrmbK'
        'YtFejbgxFwhMZxgQvqIBLsR9dAVQOhm4YTWbbIwRTemKYBpSOCO+oTrTciDFfkYOzpTZCM9G9zfEI7iFZxWYgCN1'
        '/Ybdwa+WBMFf+fK110DZ1RU9IBQgLoP2F4xk/L4p13V3VYPRw6Z93w+cD52uVkEjwcWQBXhRtH66TBSncsDMWSUD'
        'prdZynNrsqq9iROt19Vydt683+WFXUQA2RBpjmiBWg2LAjqmX10aB6515xbuvnsOmXJjL7OT2oKrgrdl65frzevL'
        '7f5CbIELwL7GAEPgpDHOn3880Zaj2Z7eblvN7cWr2wuur9rFy/1h+lG9r1thkjzPCw6F8ShBcTUtz1F3MBrnWfLl'
        'xdrQPXZOyph8JrxdMG/d5xPbcVnYDX2Zt7V6B1udYEv2wU8ujPmn350KvuAhwVSFV42NuiL4StJgbHFA8y6WlgSr'
        'wedlxZwUrvcILqQwlozMbTY8HDH4LC17QvpN9y/giw9Y'
    ),
    'docs/analytics-event-contract.md': (
        'eNqdVk1v4zYQvetXDJCr46DX9pR2N23QXXTRZA89WZQ0solQpEpSdtxTf0R/YX9J3wxlxXaDHgoYiSSS8/neG97Q'
        'z7/8dv/0Exlv3DHbNhHv2Wdqg8/RtLmqbm7oOU4pUxMm35l4rKr7y82JdmbPMEH8Ojrb2ky1LmxSmGLL9bdVdUv1'
        'ODVYrOnvP/+ir49kfWbxYIM/mTFty2PmjvoYBso7piaGQ+KI5xim7Y7qOzPau/03d0u8d+Vs/Z24wNY9x+KiC4Ox'
        'i2kebBbLwbsjNfiZ9oV9R3LCtgzffVY/TGFEXBpWmhAQd2ldVR9M2jXBxE4qAx9J1g0MNFOynlOigXOUkgxSqykx'
        'lWBuw8HD7xxGiFRqcgqvDc6xFiGt6X7JtzRBTXk8R2qYcmQjKZhEYwyhR7AmU+StTbkEvMJbG4YBic3vPcKXVGVl'
        'dKblQewmnn2uJCD07dOnz9jw+8TwNyfN3Vp7//TvLLSb5343cDo6RnC1LKkdfPbGRr5auwxws2UvxZ4XT9Fu0tSU'
        'fs1nltCvDpyvlKTmBRSot443CcAsX5wbNgJPAEc9a5opvbvWG+ckjlor8EVxK5A9S/8yR0DGv5t8yiZel2VjfDpw'
        'XFJIk8ubveXDW+zd1L77qeNsrEuLPwnvg8mGBuvtYP/Q8Kuq9OyM08Cm6XSfIioUfgN/ykwGEp3wp5+cI28Glpdx'
        'F3x5MCkdQuzk2WjR7hA0Z8oBFEr6ecq7EGf/tGPTgSFqce4ola7jDL9mNQqGj4UQAr77L4/UoiTYYo0Twn18hTYI'
        'j6LSzPjgj0OYElnd1Ft4oMEcgVslEn7RHOhz8Nvw4fuZQF1op0GJ1wvQMxjaTAX4+E+mG+QYpxH04/RWHYAhgMFI'
        'Cn/PHXZoapvdsXDjV3bWNNbZfCGKh2izKEqEfqHlt9zDexZ6Zx7GEKGhZ73pUfwJWxfnDXj+8p+8ppkFFxQnJU1K'
        '8/532T7TgkAL67fKfkCKo8AH2Gy1Fyf0lxwfNft8VL3eRk31QYqJlstKq5p0Fd+sJWk1F0+OJ8oGeHnT9gsLlXZa'
        'zMROKtU6i7VbBLyHiY7qBQAb29XUGi+lmtMsSnhyta4eTiUR5JyXYlZh63eMTN6CW2JSvbhW0Upc6Zal1iexBCqc'
        'zocnMMFmizG4cE0qW8ZbG2RiQMmT6reXIQIgYJzSCx9pb6I1Ehc0aQd5r+pCs40SrF6B/zMFNzuMIfkg1doob/Em'
        '5IEdVLsN4cWyPLxxaVWJw8K3t3hV2GLIKplktlvgDX2g7jTnqqr+8eMzLfNWqHI2dZd9teTSyAjEgJo0wTL4TsU+'
        '2Ly7HHrVxdC7llflTYviFFOjEbl3x6ICWCrzcLkqLNMQP1PNqg4h+z+DcSHI6qRLy10AJXvenZVHlCnR1+cfcPdx'
        '/a0IMmGvDV2aUdfrDr3l7NEGclAmvWFg3grURK2ubl1VBGS8QuZgfRcOa0jMSZxmxT7rlRapuAOHjAtbcqZh+JJb'
        'Ds7Cw5l4rapZhNPqJL+XQFFLC3y11sqxPEVMmzU9ROZbEXBq0WjQAcopdx5tpOxH/BhTaEoOheFLqM2E6xauheVg'
        'va7+AX4X0wE='
    ),
}


def _run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.stdout.rstrip("\n")


def _repository_root() -> Path:
    root = Path(__file__).resolve().parents[1]
    required = (
        root / "backend/app/main.py",
        root / "backend/app/services/auth_service.py",
        root / ".git",
    )
    missing = [str(path) for path in required if not path.exists()]
    if missing:
        raise RuntimeError(
            "Run this script from scripts/ inside the KOYASH repository. "
            f"Missing: {', '.join(missing)}"
        )
    return root


def _status_paths(root: Path) -> set[str]:
    output = _run_git(root, "status", "--porcelain", "--untracked-files=all")
    result: set[str] = set()
    for line in output.splitlines():
        if not line:
            continue
        path = line[3:].strip().replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        result.add(path)
    return result


def _check_preconditions(root: Path) -> None:
    branch = _run_git(root, "branch", "--show-current")
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(
            f"Expected branch {EXPECTED_BRANCH!r}, current branch is {branch!r}. "
            "Create/switch to the Step 4.9C branch before applying the patch."
        )

    unexpected = _status_paths(root) - ALLOWED_DIRTY_PATHS
    if unexpected:
        formatted = "\n  - ".join(sorted(unexpected))
        raise RuntimeError(
            "Refusing to overwrite unrelated working-tree changes:\n"
            f"  - {formatted}\n"
            "Commit, stash, or restore them first."
        )

    auth_text = (root / "backend/app/services/auth_service.py").read_text(
        encoding="utf-8-sig"
    )
    required_markers = (
        '"name_provided": bool(payload.full_name)',
        '"pre_registration_session_linked": bool(payload.anonymous_id)',
    )
    missing_markers = [
        marker for marker in required_markers if marker not in auth_text
    ]
    if missing_markers:
        raise RuntimeError(
            "Step 4.9B1 registration metadata hardening is not present. "
            "Do not apply 4.9C on an unfinished base."
        )

    hardening_test = root / "backend/tests/test_server_event_tracking_hardening.py"
    if not hardening_test.exists():
        raise RuntimeError(
            "Step 4.9B1 hardening tests are missing. Merge/restore 4.9B1 first."
        )


def _decoded_files() -> dict[str, str]:
    result: dict[str, str] = {}
    for relative_path, encoded in FILES_B64.items():
        compressed = base64.b64decode(encoded)
        result[relative_path] = zlib.decompress(compressed).decode("utf-8")
    return result


def _write_file(root: Path, relative_path: str, content: str) -> str:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized = content.replace("\r\n", "\n").replace("\r", "\n")
    normalized = normalized.rstrip() + "\n"

    if path.exists() and path.read_text(encoding="utf-8-sig") == normalized:
        return "unchanged"

    path.write_text(normalized, encoding="utf-8", newline="\n")
    return "written"


def _validate_python(root: Path, files: dict[str, str]) -> None:
    python_paths = [path for path in files if path.endswith(".py")]

    subprocess.run(
        [sys.executable, "-m", "compileall", "-q", *python_paths],
        cwd=root,
        check=True,
    )

    violations: list[str] = []
    for relative_path in python_paths:
        for line_number, line in enumerate(
            (root / relative_path).read_text(encoding="utf-8").splitlines(),
            start=1,
        ):
            if len(line) > 100:
                violations.append(
                    f"{relative_path}:{line_number}: {len(line)} characters"
                )

    if violations:
        raise RuntimeError(
            "Generated Python contains lines longer than 100 characters:\n"
            + "\n".join(violations)
        )


def main() -> int:
    root = _repository_root()
    _check_preconditions(root)
    files = _decoded_files()

    print("Applying Step 4.9C protected analytics dashboard...")
    changed = 0
    for relative_path, content in files.items():
        state = _write_file(root, relative_path, content)
        print(f"{state:9} {relative_path}")
        changed += state == "written"

    _validate_python(root, files)

    print()
    print("STEP 4.9C APPLIED")
    print("- protected /api/v1/admin/analytics/dashboard")
    print("- UTC days/date_from/date_to filters with retention validation")
    print("- overview, conversion, activity, products, feedback, replacements, audience")
    print("- server/public event separation and domain collection sources")
    print("- zero-filled empty state")
    print("- no user/anonymous IDs, comments, prompts, credentials, or raw metadata")
    print("- custom free-text restrictions reduced to aggregate bucket 'custom'")
    print("- generic 503 on unexpected dashboard aggregation failures")
    print("- legacy recent-event feed anonymized")
    print("- focused integration and privacy regression tests added")
    print(f"- files written: {changed}; unchanged: {len(files) - changed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
