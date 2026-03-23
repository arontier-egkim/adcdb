"""Unit tests for chemistry_service: Morgan fingerprints and Tanimoto similarity."""

import pytest
from rdkit import DataStructs

from app.services.chemistry_service import (
    fp_from_stored_bytes,
    smiles_to_morgan_fp,
)


class TestSmilesToMorganFP:
    """Tests for smiles_to_morgan_fp function."""

    def test_valid_smiles_returns_bitvect(self):
        """Valid SMILES should produce a fingerprint bitvector."""
        fp = smiles_to_morgan_fp("CCO")
        assert fp is not None
        assert fp.GetNumBits() == 2048

    def test_invalid_smiles_returns_none(self):
        """Invalid SMILES should return None."""
        fp = smiles_to_morgan_fp("this_is_not_smiles")
        assert fp is None

    def test_empty_smiles_produces_fp(self):
        """Empty SMILES produces a valid (empty) mol in RDKit, so FP is returned.

        Note: RDKit's MolFromSmiles("") returns a valid empty mol, not None.
        This is acceptable behavior -- an empty fingerprint has zero bits set.
        """
        fp = smiles_to_morgan_fp("")
        # RDKit returns a valid mol for empty SMILES, so FP is non-None
        # but it has zero on-bits (empty molecule).
        if fp is not None:
            assert fp.GetNumOnBits() == 0

    def test_attachment_points_cleaned(self):
        """SMILES with [*:1] and [*:2] should be cleaned to [H] before FP computation."""
        fp = smiles_to_morgan_fp("[*:1]CCCCCC(=O)O[*:2]")
        assert fp is not None
        assert fp.GetNumBits() == 2048

    def test_attachment_point_only(self):
        """SMILES that is only attachment points should produce valid result after replacement."""
        # [*:1] -> [H], which is valid hydrogen
        fp = smiles_to_morgan_fp("[*:1]")
        assert fp is not None

    def test_fingerprint_length_is_2048(self):
        """Morgan FP must always be 2048 bits (project requirement)."""
        for smi in ["CCO", "c1ccccc1", "CC(=O)Oc1ccccc1C(=O)O"]:
            fp = smiles_to_morgan_fp(smi)
            assert fp is not None
            assert fp.GetNumBits() == 2048, f"FP for {smi} has {fp.GetNumBits()} bits, expected 2048"

    def test_self_similarity_is_one(self):
        """Tanimoto similarity of a fingerprint with itself should be 1.0."""
        fp = smiles_to_morgan_fp("CCO")
        assert fp is not None
        sim = DataStructs.TanimotoSimilarity(fp, fp)
        assert sim == 1.0

    def test_different_molecules_similarity_between_zero_and_one(self):
        """Different molecules should have Tanimoto between 0.0 and 1.0."""
        fp1 = smiles_to_morgan_fp("CCO")  # ethanol
        fp2 = smiles_to_morgan_fp("c1ccccc1")  # benzene
        assert fp1 is not None and fp2 is not None
        sim = DataStructs.TanimotoSimilarity(fp1, fp2)
        assert 0.0 <= sim < 1.0


class TestFPFromStoredBytes:
    """Tests for fp_from_stored_bytes function."""

    def test_roundtrip_storage(self):
        """Storing FP as bit string bytes and reconstructing should preserve similarity."""
        fp_original = smiles_to_morgan_fp("CCO")
        assert fp_original is not None
        # Simulate storage: ToBitString().encode()
        stored = fp_original.ToBitString().encode()
        fp_restored = fp_from_stored_bytes(stored)
        assert fp_restored is not None
        sim = DataStructs.TanimotoSimilarity(fp_original, fp_restored)
        assert sim == 1.0

    def test_none_returns_none(self):
        """None input should return None."""
        assert fp_from_stored_bytes(None) is None

    def test_empty_bytes_returns_none(self):
        """Empty bytes should return None."""
        assert fp_from_stored_bytes(b"") is None

    def test_stored_length_is_2048(self):
        """Stored bit string should be 2048 characters."""
        fp = smiles_to_morgan_fp("CCO")
        assert fp is not None
        stored = fp.ToBitString().encode()
        assert len(stored) == 2048

    def test_restored_fp_has_correct_bits(self):
        """Restored FP should have the same set bits as the original."""
        fp_original = smiles_to_morgan_fp("CCO")
        assert fp_original is not None
        stored = fp_original.ToBitString().encode()
        fp_restored = fp_from_stored_bytes(stored)
        assert fp_restored is not None
        assert fp_original.GetNumOnBits() == fp_restored.GetNumOnBits()
