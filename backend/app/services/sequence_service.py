"""Sequence similarity search using Biopython PairwiseAligner."""

import re
from Bio.Align import PairwiseAligner
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Antibody

VALID_AA = set("ACDEFGHIKLMNPQRSTVWY")


def validate_sequence(seq: str) -> str | None:
    """Validate and clean an amino acid sequence. Returns None if invalid."""
    clean = re.sub(r"\s+", "", seq.upper())
    if not clean:
        return None
    if all(c in VALID_AA for c in clean):
        return clean
    return None


async def search_by_sequence(
    query_seq: str, db: AsyncSession, top_n: int = 20
) -> list[dict]:
    """Search antibodies by sequence similarity."""
    query = validate_sequence(query_seq)
    if query is None:
        return []

    aligner = PairwiseAligner()
    aligner.mode = "local"
    aligner.match_score = 2
    aligner.mismatch_score = -1
    aligner.open_gap_score = -2
    aligner.extend_gap_score = -0.5

    stmt = select(
        Antibody.id, Antibody.name, Antibody.heavy_chain_seq, Antibody.light_chain_seq
    ).where(
        (Antibody.heavy_chain_seq.is_not(None)) | (Antibody.light_chain_seq.is_not(None))
    )
    result = await db.execute(stmt)

    results = []
    for row in result:
        best_score = 0.0
        chain_matched = ""

        for chain_name, seq in [("heavy", row.heavy_chain_seq), ("light", row.light_chain_seq)]:
            if not seq:
                continue
            clean_seq = validate_sequence(seq)
            if not clean_seq:
                continue
            try:
                alignments = aligner.align(query, clean_seq)
                score = alignments.score if alignments else 0.0
                if score > best_score:
                    best_score = score
                    chain_matched = chain_name
            except Exception:
                continue

        if best_score > 0:
            # Normalize by query length
            normalized = round(best_score / (len(query) * 2), 4)  # max score per pos = 2
            results.append({
                "id": row.id,
                "name": row.name,
                "chain": chain_matched,
                "score": round(best_score, 2),
                "normalized_score": min(normalized, 1.0),
            })

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_n]
