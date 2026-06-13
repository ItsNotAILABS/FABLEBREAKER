"""Cryptographic evidence chain models.

Mathematical models for generating and verifying cryptographic evidence chains
that provide tamper-proof audit trails for benchmark certification.

Reference:
    Medina, F. (2026). Cryptographic Evidence Chains for Performance Claim
    Certification. Journal of Certification Systems, 1(1), 1-27.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class EvidenceLink:
    """A single link in the cryptographic evidence chain."""

    link_id: int
    timestamp: str
    event_type: str
    data: dict[str, Any]
    previous_hash: str
    current_hash: str = field(init=False)

    def __post_init__(self):
        """Calculate the hash for this link after initialization."""
        self.current_hash = self._calculate_hash()

    def _calculate_hash(self) -> str:
        """Calculate SHA-256 hash of this link's content."""
        # Canonical JSON representation for deterministic hashing
        canonical = {
            "link_id": self.link_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        content = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def verify(self, expected_previous_hash: str) -> bool:
        """Verify this link's integrity.

        Args:
            expected_previous_hash: Hash from the previous link.

        Returns:
            True if link is valid, False otherwise.
        """
        if self.previous_hash != expected_previous_hash:
            return False

        recalculated = self._calculate_hash()
        return recalculated == self.current_hash


@dataclass
class EvidenceChain:
    """A complete cryptographic evidence chain for benchmark certification."""

    chain_id: str
    genesis_hash: str
    links: list[EvidenceLink] = field(default_factory=list)

    def add_link(
        self,
        timestamp: str,
        event_type: str,
        data: dict[str, Any],
    ) -> EvidenceLink:
        """Add a new link to the chain.

        Args:
            timestamp: ISO 8601 timestamp.
            event_type: Type of event (e.g., "test_execution", "score_calculation").
            data: Event-specific data.

        Returns:
            The newly created EvidenceLink.
        """
        link_id = len(self.links)
        previous_hash = self.links[-1].current_hash if self.links else self.genesis_hash

        link = EvidenceLink(
            link_id=link_id,
            timestamp=timestamp,
            event_type=event_type,
            data=data,
            previous_hash=previous_hash,
        )

        self.links.append(link)
        return link

    def verify_integrity(self) -> bool:
        """Verify the integrity of the entire chain.

        Returns:
            True if all links are valid and properly connected, False otherwise.
        """
        if not self.links:
            return True  # Empty chain is valid

        # Check first link
        if not self.links[0].verify(self.genesis_hash):
            return False

        # Check all subsequent links
        for i in range(1, len(self.links)):
            expected_prev = self.links[i - 1].current_hash
            if not self.links[i].verify(expected_prev):
                return False

        return True

    def get_chain_hash(self) -> str:
        """Get the hash of the final link (representing entire chain state).

        Returns:
            Hash of the last link, or genesis hash if chain is empty.
        """
        if not self.links:
            return self.genesis_hash
        return self.links[-1].current_hash


def generate_evidence_chain(
    chain_id: str,
    events: list[tuple[str, str, dict[str, Any]]],
) -> EvidenceChain:
    """Generate a complete evidence chain from a sequence of events.

    Args:
        chain_id: Unique identifier for this chain.
        events: List of (timestamp, event_type, data) tuples.

    Returns:
        Complete EvidenceChain with all links.

    Example:
        >>> events = [
        ...     ("2026-06-01T10:00:00Z", "candidate_submission", {"candidate": "baseline"}),
        ...     ("2026-06-01T10:01:00Z", "test_execution", {"tests": 100, "passed": 95}),
        ...     ("2026-06-01T10:02:00Z", "certification", {"status": "passed"}),
        ... ]
        >>> chain = generate_evidence_chain("cert-001", events)
        >>> chain.verify_integrity()
        True
    """
    # Generate genesis hash from chain ID
    genesis_hash = hashlib.sha256(chain_id.encode("utf-8")).hexdigest()

    chain = EvidenceChain(chain_id=chain_id, genesis_hash=genesis_hash)

    for timestamp, event_type, data in events:
        chain.add_link(timestamp, event_type, data)

    return chain


def verify_evidence_chain(chain: EvidenceChain) -> tuple[bool, str]:
    """Verify an evidence chain and return detailed status.

    Args:
        chain: The EvidenceChain to verify.

    Returns:
        Tuple of (is_valid, message) describing verification result.

    Example:
        >>> chain = generate_evidence_chain("test", [
        ...     ("2026-06-01T10:00:00Z", "event", {"data": "test"}),
        ... ])
        >>> is_valid, msg = verify_evidence_chain(chain)
        >>> is_valid
        True
    """
    if not chain.links:
        return True, "Empty chain (valid)"

    # Verify genesis link
    if chain.links[0].previous_hash != chain.genesis_hash:
        return False, "Genesis link does not reference correct genesis hash"

    # Verify each link
    for i, link in enumerate(chain.links):
        expected_prev = chain.genesis_hash if i == 0 else chain.links[i - 1].current_hash

        if not link.verify(expected_prev):
            return False, f"Link {i} failed verification"

        # Verify link ID sequence
        if link.link_id != i:
            return False, f"Link {i} has incorrect ID {link.link_id}"

    return True, f"Chain valid with {len(chain.links)} links"


def chain_integrity_proof(chain: EvidenceChain) -> dict[str, Any]:
    """Generate a compact integrity proof for an evidence chain.

    The proof includes key hashes that allow verification without revealing
    all intermediate data.

    Args:
        chain: The EvidenceChain to prove.

    Returns:
        Integrity proof dictionary.

    Example:
        >>> chain = generate_evidence_chain("test", [
        ...     ("2026-06-01T10:00:00Z", "event", {"data": "test"}),
        ... ])
        >>> proof = chain_integrity_proof(chain)
        >>> "genesis_hash" in proof
        True
    """
    proof = {
        "chain_id": chain.chain_id,
        "genesis_hash": chain.genesis_hash,
        "chain_length": len(chain.links),
        "final_hash": chain.get_chain_hash(),
        "merkle_root": _calculate_merkle_root(chain),
    }

    # Include hashes of first and last links for quick verification
    if chain.links:
        proof["first_link_hash"] = chain.links[0].current_hash
        proof["last_link_hash"] = chain.links[-1].current_hash

    return proof


def _calculate_merkle_root(chain: EvidenceChain) -> str:
    """Calculate Merkle root of all link hashes.

    Args:
        chain: The evidence chain.

    Returns:
        Merkle root hash.
    """
    if not chain.links:
        return chain.genesis_hash

    # Collect all link hashes
    hashes = [link.current_hash for link in chain.links]

    # Build Merkle tree
    while len(hashes) > 1:
        next_level = []
        for i in range(0, len(hashes), 2):
            if i + 1 < len(hashes):
                # Pair hashes and hash them together
                combined = hashes[i] + hashes[i + 1]
                parent = hashlib.sha256(combined.encode("utf-8")).hexdigest()
                next_level.append(parent)
            else:
                # Odd one out, promote to next level
                next_level.append(hashes[i])
        hashes = next_level

    return hashes[0]


def chain_append_proof(
    original_proof: dict[str, Any],
    new_links: list[EvidenceLink],
) -> dict[str, Any]:
    """Prove that new links extend an existing chain.

    Args:
        original_proof: Integrity proof of the original chain.
        new_links: New links to append.

    Returns:
        Updated integrity proof.

    Example:
        >>> chain = generate_evidence_chain("test", [
        ...     ("2026-06-01T10:00:00Z", "event1", {}),
        ... ])
        >>> proof1 = chain_integrity_proof(chain)
        >>> chain.add_link("2026-06-01T10:01:00Z", "event2", {})
        EvidenceLink(...)
        >>> proof2 = chain_integrity_proof(chain)
        >>> proof2["chain_length"] == proof1["chain_length"] + 1
        True
    """
    if not new_links:
        return original_proof

    # Verify new links build on original chain
    expected_prev = original_proof["final_hash"]
    for link in new_links:
        if link.previous_hash != expected_prev:
            raise ValueError(f"Link {link.link_id} does not connect to chain")
        expected_prev = link.current_hash

    # Generate updated proof
    return {
        "chain_id": original_proof["chain_id"],
        "genesis_hash": original_proof["genesis_hash"],
        "chain_length": original_proof["chain_length"] + len(new_links),
        "final_hash": new_links[-1].current_hash,
        "original_final_hash": original_proof["final_hash"],
        "extension_length": len(new_links),
    }
