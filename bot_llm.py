import chess
import random
import time
from typing import Optional, Dict, Any

from src.api_manager import chat_completion


class LLMBot:
    def __init__(self, api_key: str, model_name: str, provider: str = "openai",
                 base_url: str = None, color: chess.Color = chess.WHITE):
        self.api_key = api_key
        self.model_name = model_name
        self.provider = provider
        self.base_url = base_url or "https://api.openai.com/v1"
        self.color = color
        self.max_retries = 3

    def get_move(self, board: chess.Board) -> chess.Move:
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            return None

        fen = board.fen()
        legal_uci_list = ", ".join(sorted(m.uci() for m in legal_moves))

        system_prompt = (
            "You are a chess engine. Given a FEN position, return ONLY the "
            "UCI notation of the move you want to make (e.g., e2e4). "
            "Do NOT include any explanation, text, punctuation, or other characters."
        )

        messages = [
            {"role": "system", "content": system_prompt},
{"role": "user", "content": f"FEN: {fen}\nLegal moves: {legal_uci_list}"},
        ]

        results = {
            "tokens_in": 0,
            "tokens_out": 0,
            "retries": 0,
            "illegal_attempts": [],
            "api_error": None,
            "fallback": False,
        }

        for attempt in range(1, self.max_retries + 1):
            results["retries"] = attempt - 1

            content, stats = chat_completion(
                provider=self.provider,
                api_key=self.api_key,
                model=self.model_name,
                messages=messages,
                temperature=0.1,
                max_tokens=10,
                timeout=30,
            )

            results["tokens_in"] = stats.get("tokens_in", 0)
            results["tokens_out"] = stats.get("tokens_out", 0)

            if content is None:
                results["api_error"] = stats.get("error", "Unknown error")
                continue

            uci = content.strip().replace(" ", "").replace("\n", "")
            uci = "".join(c for c in uci if c.isalnum())

            try:
                move = chess.Move.from_uci(uci)
            except ValueError:
                results["illegal_attempts"].append(content)
                messages.append({"role": "user", "content": f"Illegal move: {uci}. Only give a legal UCI move."})
                continue

            if board.is_legal(move):
                self._last_stats = results
                return move
            else:
                results["illegal_attempts"].append(content)
                messages.append({"role": "user", "content": f"Illegal move: {uci}. Must be from: {legal_uci_list}"})

        fallback = random.choice(legal_moves)
        results["fallback"] = True
        self._last_stats = results
        return fallback

    def get_stats(self) -> Dict[str, Any]:
        return getattr(self, "_last_stats", {})