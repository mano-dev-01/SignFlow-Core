import json
import threading
import uuid
from collections import deque
from datetime import datetime, timezone
from overlay_paths import get_logs_dir


class CaptionLogger:
    def __init__(
        self,
        is_simulation: bool,
        llm_smoothing_enabled: bool,
        model_name: str | None = None,
    ):
        self._is_simulation = bool(is_simulation)
        prefix = "pseudo-" if self._is_simulation else ""
        self._session_id = f"{prefix}{uuid.uuid4().hex[:8]}"
        self._model_name = model_name or ("debug_random_generator" if self._is_simulation else "unknown")
        self._llm_smoothing_enabled = bool(llm_smoothing_enabled)

        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._payload = {
            "session_id": self._session_id,
            "start_time": now,
            "model_name": self._model_name,
            "llm_smoothing_enabled": self._llm_smoothing_enabled,
            "is_simulation": self._is_simulation,
            "final_caption_text": "",
            "events": [],
        }

        self._events = self._payload["events"]
        self._queue = deque()
        self._lock = threading.Lock()
        self._event = threading.Event()
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)

        log_dir = get_logs_dir()
        self._log_path = log_dir / f"{self._session_id}.json"
        self._write_payload()
        self._thread.start()

    @property
    def session_id(self):
        return self._session_id

    def update_model_name(self, model_name: str | None):
        if not model_name:
            return
        if model_name == self._model_name:
            return
        with self._lock:
            self._model_name = str(model_name)
            self._payload["model_name"] = self._model_name
        self._event.set()

    def update_llm_smoothing(self, enabled: bool):
        enabled = bool(enabled)
        if enabled == self._llm_smoothing_enabled:
            return
        with self._lock:
            self._llm_smoothing_enabled = enabled
            self._payload["llm_smoothing_enabled"] = enabled
        self._event.set()

    def log_event(
        self,
        tokens_predicted: list[str],
        raw_output: str,
        smoothed_output: str,
        prediction_latency_ms: float,
        model_name: str | None = None,
        llm_smoothing_enabled: bool | None = None,
    ):
        timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        event = {
            "timestamp": timestamp,
            "tokens_predicted": list(tokens_predicted or []),
            "raw_output": raw_output or "",
            "smoothed_output": smoothed_output or "",
            "prediction_latency_ms": float(prediction_latency_ms or 0.0),
            "model_name": model_name or self._model_name,
            "llm_smoothing_enabled": self._llm_smoothing_enabled
            if llm_smoothing_enabled is None
            else bool(llm_smoothing_enabled),
        }
        with self._lock:
            self._queue.append(event)
        self._event.set()

    def set_final_caption(self, text: str | None):
        new_text = text or ""
        with self._lock:
            if self._payload.get("final_caption_text") == new_text:
                return
            self._payload["final_caption_text"] = new_text
        self._event.set()

    def stop(self):
        self._running = False
        self._event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=0.5)
        self._write_payload()

    def _run(self):
        while self._running:
            self._event.wait(0.5)
            self._event.clear()
            self._drain_queue()
            self._write_payload()
        self._drain_queue()
        self._write_payload()

    def _drain_queue(self):
        with self._lock:
            while self._queue:
                self._events.append(self._queue.popleft())

    def _write_payload(self):
        try:
            self._log_path.write_text(json.dumps(self._payload, indent=2), encoding="utf-8")
        except Exception:
            pass
