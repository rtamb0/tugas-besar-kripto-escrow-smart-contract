from dataclasses import dataclass
from typing import Optional


@dataclass
class Block:
    height: int
    timestamp: str
    transactions: list
    prev_hash: str
    nonce: int
    difficulty: int
    block_hash: str
    state_root: Optional[str] = None

    def to_dict(self) -> dict:
        data = {
            "height": self.height,
            "timestamp": self.timestamp,
            "transactions": self.transactions,
            "prev_hash": self.prev_hash,
            "nonce": self.nonce,
            "difficulty": self.difficulty,
            "state_root": self.state_root,
            "block_hash": self.block_hash,
        }

        return {key: value for key, value in data.items() if value is not None}

    @staticmethod
    def from_dict(data: dict) -> "Block":
        return Block(
            height=data["height"],
            timestamp=data["timestamp"],
            transactions=data.get("transactions", []),
            prev_hash=data["prev_hash"],
            nonce=data.get("nonce", 0),
            difficulty=data.get("difficulty", 2),
            state_root=data.get("state_root"),
            block_hash=data["block_hash"],
        )
