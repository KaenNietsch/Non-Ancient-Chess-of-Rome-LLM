import json
import os
import time
from typing import Any, Dict, List, Optional
from datetime import datetime


HISTORY_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "match_history.json")


class StatsTracker:
    def __init__(self, white_name: str, black_name: str, mode: str):
        self.match_id = f"match_{int(time.time())}_{os.urandom(4).hex()}"
        self.white_name = white_name
        self.black_name = black_name
        self.mode = mode
        self.started_at = datetime.now().isoformat()
        self.moves: List[Dict[str, Any]] = []
        self.result = None
        self.termination = None
        self.total_illegal_moves = 0
        self.llm_disqualification = None

    def record_move(self, data: Dict[str, Any]) -> None:
        record = {
            "ply": data["ply"],
            "color": data["color"],
            "move_uci": data["move_uci"] if data.get("move_uci") else None,
            "move_san": data.get("move_san", ""),
            "player": data.get("player", "unknown"),
            "is_legal": data.get("is_legal", True),
            "latency_ms": data.get("latency_ms", 0),
        }
        if data.get("eval_score") is not None:
            record["eval_score"] = data["eval_score"]
        if data.get("tokens_in"):
            record["tokens_in"] = data["tokens_in"]
        if data.get("tokens_out"):
            record["tokens_out"] = data["tokens_out"]
        if data.get("retries"):
            record["retries"] = data["retries"]
        if data.get("illegal_attempts"):
            record["illegal_attempts"] = data["illegal_attempts"]
            self.total_illegal_moves += len(data["illegal_attempts"])
        if data.get("api_error"):
            record["api_error"] = data["api_error"]
        if data.get("fallback"):
            record["fallback"] = data["fallback"]
        self.moves.append(record)

    def set_result(self, winner: str, termination: str, disqualify_reason: str = None) -> None:
        self.result = winner
        self.termination = termination
        if disqualify_reason:
            self.llm_disqualification = disqualify_reason

    def finalize(self) -> Dict[str, Any]:
        total_latency_w = 0
        total_latency_b = 0
        count_w = 0
        count_b = 0
        total_tokens_in = 0
        total_tokens_out = 0
        total_retries = 0

        for m in self.moves:
            lat = m.get("latency_ms", 0) or 0
            if m["color"] == "white":
                total_latency_w += lat
                count_w += 1
            else:
                total_latency_b += lat
                count_b += 1
            total_tokens_in += m.get("tokens_in", 0) or 0
            total_tokens_out += m.get("tokens_out", 0) or 0
            total_retries += m.get("retries", 0) or 0

        summary = {
            "match_id": self.match_id,
            "white": self.white_name,
            "black": self.black_name,
            "mode": self.mode,
            "started_at": self.started_at,
            "finished_at": datetime.now().isoformat(),
            "result": self.result,
            "termination": self.termination,
            "total_moves": len(self.moves),
            "total_illegal_moves": self.total_illegal_moves,
            "llm_disqualification": self.llm_disqualification,
            "avg_latency_white_ms": int(total_latency_w / count_w) if count_w > 0 else 0,
            "avg_latency_black_ms": int(total_latency_b / count_b) if count_b > 0 else 0,
            "total_tokens_in": total_tokens_in,
            "total_tokens_out": total_tokens_out,
            "total_retries": total_retries,
            "moves": self.moves,
        }
        self._save_to_history(summary)
        return summary

    def _save_to_history(self, summary: Dict[str, Any]) -> None:
        history = []
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            history = []

        history.append(summary)

        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)


def load_match_history() -> List[Dict[str, Any]]:
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def get_match(match_id: str) -> Dict[str, Any]:
    history = load_match_history()
    for m in history:
        if m.get("match_id") == match_id:
            return m
    return {}