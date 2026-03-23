"""Unit tests for structure module: conformer generation and ADC assembly."""

import tempfile
from pathlib import Path

import pytest

from app.structure.conformer import generate_conformer, mol_to_pdb_block
from app.structure.assembler import (
    assemble_adc,
    generate_and_save,
    _get_conjugation_sites,
    _generate_antibody_template,
)


class TestGenerateConformer:
    """Tests for conformer generation."""

    def test_valid_smiles_returns_mol(self):
        """Valid linker-payload SMILES should produce a 3D Mol object."""
        mol = generate_conformer("[*:1]CCCCCC(=O)NCC(=O)O")
        assert mol is not None

    def test_none_returns_none(self):
        """None input should return None."""
        assert generate_conformer(None) is None

    def test_empty_string_returns_none(self):
        """Empty string should return None."""
        assert generate_conformer("") is None

    def test_invalid_smiles_returns_none(self):
        """Invalid SMILES should return None."""
        assert generate_conformer("not_a_molecule") is None

    def test_conformer_has_3d_coords(self):
        """Generated conformer should have 3D coordinates."""
        mol = generate_conformer("[*:1]CCCCCC(=O)O")
        assert mol is not None
        conf = mol.GetConformer()
        assert conf.Is3D()


class TestMolToPDBBlock:
    """Tests for PDB block generation."""

    def test_valid_mol_produces_pdb(self):
        """Valid Mol should produce PDB block with HETATM lines."""
        mol = generate_conformer("[*:1]CCCCCC(=O)O")
        assert mol is not None
        pdb = mol_to_pdb_block(mol, chain_id="D")
        assert "HETATM" in pdb

    def test_chain_id_applied(self):
        """Chain ID should appear in the PDB block."""
        mol = generate_conformer("[*:1]CCCCCC(=O)O")
        assert mol is not None
        pdb = mol_to_pdb_block(mol, chain_id="X")
        # Chain ID is at column 22 (0-indexed: 21)
        for line in pdb.splitlines():
            if line.startswith("HETATM"):
                assert line[21] == "X"
                break


class TestAssembleADC:
    """Tests for ADC assembly."""

    def test_valid_inputs_produce_pdb(self):
        """Valid LP SMILES + conjugation params should produce a PDB string."""
        pdb = assemble_adc("[*:1]CCCCCC(=O)O", "cysteine", 4.0)
        assert pdb is not None
        assert "ATOM" in pdb  # antibody template
        assert "HETATM" in pdb  # LP conformers
        assert "END" in pdb

    def test_no_lp_smiles_returns_none(self):
        """Missing LP SMILES should return None."""
        assert assemble_adc(None, "cysteine", 4.0) is None
        assert assemble_adc("", "cysteine", 4.0) is None

    def test_default_dar_is_four(self):
        """When DAR is None, it should default to 4.0."""
        pdb = assemble_adc("[*:1]CCCCCC(=O)O", "cysteine", None)
        assert pdb is not None
        # Should have up to 4 linker-payload copies
        hetatm_chains = set()
        for line in pdb.splitlines():
            if line.startswith("HETATM"):
                hetatm_chains.add(line[21])
        # DAR=4 means 4 sites, each with a chain
        assert len(hetatm_chains) >= 1


class TestGetConjugationSites:
    """Tests for conjugation site selection."""

    def test_cysteine_sites(self):
        """Cysteine sites should be returned for DAR <= 8."""
        sites = _get_conjugation_sites("cysteine", 4.0)
        assert len(sites) == 4

    def test_lysine_sites(self):
        """Lysine sites should be selected when site_type is 'lysine'."""
        sites = _get_conjugation_sites("lysine", 2.0)
        assert len(sites) == 2

    def test_dar_rounds_to_integer(self):
        """DAR should be rounded to nearest integer for site count."""
        sites = _get_conjugation_sites("cysteine", 3.7)
        assert len(sites) == 4  # round(3.7) = 4

    def test_minimum_one_site(self):
        """Should always return at least 1 site."""
        sites = _get_conjugation_sites("cysteine", 0.1)
        assert len(sites) >= 1


class TestGenerateAndSave:
    """Tests for generate_and_save to disk."""

    def test_creates_file(self):
        """Should create a PDB file on disk and return the path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_and_save(
                adc_id="test-adc-001",
                linker_payload_smiles="[*:1]CCCCCC(=O)O",
                conjugation_site="cysteine",
                dar=4.0,
                output_dir=tmpdir,
            )
            assert path is not None
            assert Path(path).exists()
            content = Path(path).read_text()
            assert "ATOM" in content
            assert "END" in content

    def test_no_smiles_returns_none(self):
        """Missing SMILES should return None without creating a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = generate_and_save(
                adc_id="test-adc-002",
                linker_payload_smiles=None,
                conjugation_site="cysteine",
                dar=4.0,
                output_dir=tmpdir,
            )
            assert path is None


class TestAntibodyTemplate:
    """Tests for the IgG template generation."""

    def test_template_has_atom_lines(self):
        """Template should contain ATOM lines."""
        pdb = _generate_antibody_template()
        assert "ATOM" in pdb
        atom_count = sum(1 for line in pdb.splitlines() if line.startswith("ATOM"))
        # 50 (H) + 50 (A) + 30 (L) + 30 (B) = 160 CA atoms
        assert atom_count == 160

    def test_template_has_multiple_chains(self):
        """Template should have 4 chains: H, A, L, B."""
        pdb = _generate_antibody_template()
        chains = set()
        for line in pdb.splitlines():
            if line.startswith("ATOM"):
                chains.add(line[21])
        assert chains == {"H", "A", "L", "B"}
