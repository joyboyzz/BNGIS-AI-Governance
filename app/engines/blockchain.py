"""
BNGIS — Transparency Blockchain Layer (TBL)
===========================================
Lightweight hash-chain (Module 7 of spec). NO mining, NO cryptocurrency —
just SHA-256 hash chaining for immutable, auditable governance records.

Every scheme match / corruption report / decision is appended as a block.
Chain persists to app/data/chain.json.
"""

import hashlib
import json
import os
from datetime import datetime, timezone

CHAIN_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "chain.json")


class GovernanceBlock:
    def __init__(self, index, block_type, data, previous_hash):
        self.index = index
        self.timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00","Z")
        self.block_type = block_type
        self.data = data
        self.previous_hash = previous_hash
        self.nonce = 0
        self.hash = self.calculate_hash()

    def calculate_hash(self):
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "type": self.block_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "type": self.block_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "hash": self.hash,
        }


class GovernanceChain:
    def __init__(self):
        self.chain = self._load()
        if not self.chain:
            genesis = GovernanceBlock(0, "GENESIS",
                                      {"message": "BNGIS Genesis Block — Transparency for Bharat"}, "0")
            self.chain = [genesis.to_dict()]
            self._save()

    def _load(self):
        if os.path.exists(CHAIN_PATH):
            try:
                with open(CHAIN_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list) and data:
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return None

    def _save(self):
        with open(CHAIN_PATH, "w", encoding="utf-8") as f:
            json.dump(self.chain, f, indent=1)

    def add(self, block_type: str, data: dict) -> dict:
        block = GovernanceBlock(
            index=len(self.chain),
            block_type=block_type,
            data=data,
            previous_hash=self.chain[-1]["hash"],
        )
        self.chain.append(block.to_dict())
        self._save()
        return block.to_dict()

    def _verify_list(self, blocks) -> dict:
        for i in range(1, len(blocks)):
            cur = blocks[i]
            block_string = json.dumps({
                "index": cur["index"],
                "timestamp": cur["timestamp"],
                "type": cur["type"],
                "data": cur["data"],
                "previous_hash": cur["previous_hash"],
                "nonce": cur.get("nonce", 0),
            }, sort_keys=True)
            recomputed_hash = hashlib.sha256(block_string.encode()).hexdigest()
            if recomputed_hash != cur["hash"]:
                return {"valid": False, "broken_at": i,
                        "message": f"Block {i} hash mismatch — TAMPERED! "
                                   f"Recorded data was modified after signing."}
            if cur["previous_hash"] != blocks[i - 1]["hash"]:
                return {"valid": False, "broken_at": i,
                        "message": f"Block {i} chain break — TAMPERED!"}
        return {"valid": True, "blocks": len(blocks),
                "message": f"Chain integrity verified across {len(blocks)} blocks \u2705"}

    def verify(self) -> dict:
        """Verify against the PERSISTED chain (source of truth on disk),
        so any after-the-fact edit of the ledger is caught."""
        disk = self._load()
        blocks = disk if disk else self.chain
        return self._verify_list(blocks)

    def tamper(self, index: int = 1) -> dict:
        """DEMO ONLY: simulate an attacker editing a signed record on disk."""
        disk = self._load() or [b for b in self.chain]
        if len(disk) <= index:
            return {"tampered": False, "message": "not enough blocks"}
        disk[index]["data"]["__ATTACKER_EDIT__"] = "diverted funds"
        disk[index]["data"]["amount"] = 99999999
        with open(CHAIN_PATH, "w", encoding="utf-8") as f:
            json.dump(disk, f, indent=1)
        return {"tampered": True, "block": index,
                "message": f"Block {index} was edited by an attacker"}

    def repair(self) -> dict:
        """Restore the ledger from the in-memory (authentic) chain."""
        self._save()
        return self.verify()

    def list(self, limit=50):
        return list(reversed(self.chain[-limit:]))
