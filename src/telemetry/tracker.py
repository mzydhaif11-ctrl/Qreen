"""
Qreen Contextual Engine | Anonymous Telemetry Tracker
======================================================
تتبع مجهول لتحسين النظام تلقائياً — لا نص استعلام، لا هوية مستخدم، لا IP 🔒🇸🇦

Author: Qreen Team
License: MIT
"""

from __future__ import annotations

import json
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TelemetryTracker:
    """
    نظام تتبع مجهول لتحسين النظام تلقائياً.
    يسجّل إحصائيات رقمية فقط — بدون نصوص أو هويات.
    """

    def __init__(self, data_dir: Optional[str] = None):
        self._data_dir = Path(data_dir) if data_dir else Path(".telemetry_data")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._data_dir / "events.jsonl"
        self._start_time = time.time()

    def track_query(self, query_length: int, results_found: int, duration_ms: float = 0.0) -> None:
        """تسجيل حدث استعلام مجهول"""
        event = {
            "type": "query",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "query_length": query_length,
            "results_found": results_found,
            "duration_ms": round(duration_ms, 2),
        }
        self._write_event(event)

    def track_error(self, error_type: str, module: str) -> None:
        """تسجيل خطأ مجهول"""
        event = {
            "type": "error",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error_type": error_type,
            "module": module,
        }
        self._write_event(event)

    def track_memory_operation(self, operation: str, items_affected: int) -> None:
        """تسجيل عملية ذاكرة مجهولة"""
        event = {
            "type": "memory_op",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "operation": operation,
            "items_affected": items_affected,
        }
        self._write_event(event)

    def _write_event(self, event: dict) -> None:
        """كتابة حدث في ملف JSONL محلي"""
        try:
            with open(self._log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(event, ensure_ascii=False) + "\n")
        except OSError as e:
            logger.warning(f"Failed to write telemetry event: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """إحصائيات عامة من بيانات التتبع"""
        if not self._log_file.exists():
            return {"total_events": 0, "uptime_seconds": round(time.time() - self._start_time, 2)}

        events = []
        try:
            with open(self._log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        events.append(json.loads(line))
        except (json.JSONDecodeError, OSError):
            pass

        queries = [e for e in events if e.get("type") == "query"]
        errors = [e for e in events if e.get("type") == "error"]
        memory_ops = [e for e in events if e.get("type") == "memory_op"]

        avg_results = (
            sum(q.get("results_found", 0) for q in queries) / max(len(queries), 1)
        )

        return {
            "total_events": len(events),
            "total_queries": len(queries),
            "total_errors": len(errors),
            "total_memory_ops": len(memory_ops),
            "avg_results_per_query": round(avg_results, 2),
            "uptime_seconds": round(time.time() - self._start_time, 2),
        }

    def reset(self) -> int:
        """مسح جميع بيانات التتبع"""
        if self._log_file.exists():
            count = sum(1 for _ in open(self._log_file, "r"))
            self._log_file.unlink()
            logger.info(f"🗑️ Telemetry reset: {count} events cleared")
            return count
        return 0