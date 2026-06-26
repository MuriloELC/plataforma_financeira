#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
from typing import Any
import warnings

from fastapi.testclient import TestClient

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings
from app.main import create_app


warnings.filterwarnings(
    "ignore",
    message="Workbook contains no default style.*",
    category=UserWarning,
    module="openpyxl.styles.stylesheet",
)

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".pdf"}
CONTENT_TYPES = {
    ".csv": "text/csv",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pdf": "application/pdf",
}


def _counter_dict(counter: Counter[str]) -> dict[str, int]:
    return dict(sorted(counter.items()))


def _post_file(client: TestClient, path: Path) -> tuple[int, dict[str, Any] | None]:
    with path.open("rb") as file_handle:
        response = client.post(
            "/files/upload",
            files={
                "file": (
                    path.name,
                    file_handle,
                    CONTENT_TYPES.get(path.suffix.lower(), "application/octet-stream"),
                )
            },
        )
    try:
        body = response.json()
    except ValueError:
        body = None
    return response.status_code, body if isinstance(body, dict) else None


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Valida arquivos oficiais localmente e imprime apenas metricas agregadas."
    )
    parser.add_argument("--source", required=True, help="Diretorio local montado como read-only no container.")
    parser.add_argument("--reference-date", default=date.today().isoformat())
    args = parser.parse_args()

    source = Path(args.source)
    metrics: dict[str, Any] = {
        "total_files": 0,
        "by_extension": {},
        "unsupported_extensions": {},
        "uploads": {
            "by_http_status": {},
            "by_batch_status": {},
            "by_source_type": {},
            "duplicates": 0,
        },
        "previews": {
            "success": 0,
            "failed": 0,
            "by_http_status": {},
            "by_source_type": {},
        },
        "approvals": {
            "success": 0,
            "failed": 0,
            "by_http_status": {},
            "by_source_type": {},
        },
        "gold_refresh": {
            "attempted": False,
            "http_status": None,
            "ok": False,
        },
    }

    if not source.exists() or not source.is_dir():
        metrics["error"] = "source_directory_unavailable"
        print(json.dumps(metrics, ensure_ascii=True, sort_keys=True))
        return 1

    files = sorted(path for path in source.rglob("*") if path.is_file())
    by_extension = Counter(path.suffix.lower() or "<none>" for path in files)
    unsupported = Counter(
        extension for extension, count in by_extension.items() for _ in range(count) if extension not in SUPPORTED_EXTENSIONS
    )
    metrics["total_files"] = len(files)
    metrics["by_extension"] = _counter_dict(by_extension)
    metrics["unsupported_extensions"] = _counter_dict(unsupported)

    with TemporaryDirectory(prefix="official-validation-") as storage_dir:
        os.environ["FILE_STORAGE_PATH"] = storage_dir
        get_settings.cache_clear()
        client = TestClient(create_app())

        upload_http = Counter()
        upload_status = Counter()
        upload_source = Counter()
        preview_http = Counter()
        preview_source = Counter()
        approval_http = Counter()
        approval_source = Counter()
        approved_any = False

        for path in files:
            extension = path.suffix.lower()
            if extension not in SUPPORTED_EXTENSIONS:
                continue

            status_code, body = _post_file(client, path)
            upload_http[str(status_code)] += 1
            if status_code != 201 or body is None:
                continue

            batch = body.get("import_batch", {})
            raw_file = body.get("raw_file", {})
            source_type = str(batch.get("source_type") or raw_file.get("source_type") or "unknown")
            batch_status = str(batch.get("status") or "unknown")
            upload_status[batch_status] += 1
            upload_source[source_type] += 1
            if body.get("duplicate") is True:
                metrics["uploads"]["duplicates"] += 1

            batch_id = batch.get("id")
            if not batch_id:
                continue

            preview_response = client.get(f"/import-batches/{batch_id}/preview")
            preview_http[str(preview_response.status_code)] += 1
            preview_source[source_type] += 1
            if preview_response.status_code == 200:
                metrics["previews"]["success"] += 1
            else:
                metrics["previews"]["failed"] += 1
                continue

            approval_response = client.post(f"/import-batches/{batch_id}/approve")
            approval_http[str(approval_response.status_code)] += 1
            approval_source[source_type] += 1
            if approval_response.status_code == 200:
                metrics["approvals"]["success"] += 1
                approved_any = True
            else:
                metrics["approvals"]["failed"] += 1

        metrics["uploads"]["by_http_status"] = _counter_dict(upload_http)
        metrics["uploads"]["by_batch_status"] = _counter_dict(upload_status)
        metrics["uploads"]["by_source_type"] = _counter_dict(upload_source)
        metrics["previews"]["by_http_status"] = _counter_dict(preview_http)
        metrics["previews"]["by_source_type"] = _counter_dict(preview_source)
        metrics["approvals"]["by_http_status"] = _counter_dict(approval_http)
        metrics["approvals"]["by_source_type"] = _counter_dict(approval_source)

        if approved_any:
            response = client.post(f"/gold/refresh?reference_date={args.reference_date}")
            metrics["gold_refresh"] = {
                "attempted": True,
                "http_status": response.status_code,
                "ok": response.status_code == 200,
            }

    print(json.dumps(metrics, ensure_ascii=True, sort_keys=True))
    has_failures = (
        bool(unsupported)
        or metrics["previews"]["failed"] > 0
        or metrics["approvals"]["failed"] > 0
        or (metrics["gold_refresh"]["attempted"] and not metrics["gold_refresh"]["ok"])
    )
    return 2 if has_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
