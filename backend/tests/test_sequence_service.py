"""Unit tests for sequence_service: amino acid validation and alignment."""

import pytest

from app.services.sequence_service import validate_sequence, VALID_AA


class TestValidateSequence:
    """Tests for validate_sequence function."""

    def test_valid_sequence(self):
        """Standard amino acid sequence should be accepted."""
        result = validate_sequence("EVQLVESGGGLVQ")
        assert result == "EVQLVESGGGLVQ"

    def test_lowercase_converted_to_uppercase(self):
        """Lowercase input should be uppercased."""
        result = validate_sequence("evqlvesggglvq")
        assert result == "EVQLVESGGGLVQ"

    def test_whitespace_stripped(self):
        """Whitespace should be removed from sequence."""
        result = validate_sequence("EVQ LVE SGG")
        assert result == "EVQLVESGG"

    def test_newlines_stripped(self):
        """Newlines (FASTA-style) should be removed."""
        result = validate_sequence("EVQL\nVESG\nGGLVQ")
        assert result == "EVQLVESGGGLVQ"

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert validate_sequence("") is None

    def test_whitespace_only_returns_none(self):
        """Whitespace-only string should return None."""
        assert validate_sequence("   \n\t  ") is None

    def test_invalid_characters_returns_none(self):
        """Sequence with digits or special characters should return None."""
        assert validate_sequence("EVQLV123") is None
        assert validate_sequence("EVQLV*ESG") is None
        assert validate_sequence("EVQLV-ESG") is None

    def test_all_20_standard_amino_acids(self):
        """All 20 standard amino acids should be accepted."""
        all_aa = "ACDEFGHIKLMNPQRSTVWY"
        result = validate_sequence(all_aa)
        assert result == all_aa

    def test_valid_aa_set_has_20_members(self):
        """The VALID_AA set should contain exactly 20 standard amino acids."""
        assert len(VALID_AA) == 20

    def test_non_standard_amino_acids_rejected(self):
        """Non-standard amino acids (B, J, O, U, X, Z) should cause rejection."""
        for bad in ["B", "J", "O", "U", "X", "Z"]:
            result = validate_sequence(f"EVQLVE{bad}SGG")
            assert result is None, f"Sequence with '{bad}' should be rejected"
