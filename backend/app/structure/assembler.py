"""Assemble ADC 3D structure: IgG1 crystal template (PDB 1HZH) + linker-payload conformers."""

from pathlib import Path

from app.structure.conformer import generate_conformer, mol_to_pdb_block

# Path to the IgG1 crystal structure template
_TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_TEMPLATE_PDB = _TEMPLATE_DIR / "1HZH.pdb"

# Chain ID mapping from 1HZH original chains to ADCDB convention:
#   1HZH: H (heavy1), K (heavy2), L (light1), M (light2)
#   ADCDB: H (heavy1), A (heavy2), L (light1), B (light2)
_CHAIN_MAP = {"H": "H", "K": "A", "L": "L", "M": "B"}

# Interchain disulfide CYS positions from 1HZH (SG atom coordinates).
# For cysteine-conjugated ADCs, these are the hinge-region CYS residues
# whose disulfide bonds are reduced for drug attachment.
#   H239, H242 (heavy chain 1 hinge)
#   K239, K242 (heavy chain 2 hinge, mapped to chain A)
# For higher DAR, include Fab H-L and K-M interchain CYS:
#   H230 (Fab1 HC-LC), K230 (Fab2 HC-LC)
#   L214 (Fab1 LC), M214 (Fab2 LC)
CYSTEINE_SITES = [
    # Hinge region (typical DAR=4 sites)
    (72.024, 110.104, 140.627),   # H CYS239 SG
    (80.807, 112.237, 133.426),   # H CYS242 SG
    (70.513, 110.555, 141.931),   # K(A) CYS239 SG
    (62.272, 113.722, 132.960),   # K(A) CYS242 SG
    # Fab interchain (DAR=8 sites)
    (71.998, 108.603, 157.211),   # H CYS230 SG (Fab1 HC-LC)
    (85.924, 104.062, 140.468),   # K(A) CYS230 SG (Fab2 HC-LC)
    (73.360, 107.108, 157.004),   # L CYS214 SG (Fab1 LC)
    (87.636, 104.536, 141.459),   # M(B) CYS214 SG (Fab2 LC)
]

# Surface-exposed LYS residue positions from 1HZH (NZ atom coordinates).
# Selected to be distributed across all four chains and different domains.
LYSINE_SITES = [
    (125.284, 117.094, 203.118),  # H LYS57 NZ  (Fab1 VH)
    (103.323, 65.940, 87.491),    # K(A) LYS57 NZ  (Fab2 VH)
    (91.735, 128.795, 197.697),   # L LYS39 NZ  (Fab1 VL)
    (76.648, 86.684, 99.325),     # M(B) LYS39 NZ  (Fab2 VL)
    (56.727, 138.350, 120.582),   # H LYS259 NZ (Fc CH2)
    (35.740, 117.102, 108.405),   # K(A) LYS259 NZ (Fc CH2)
    (101.603, 130.571, 190.989),  # H LYS105 NZ (Fab1 CH1)
    (82.960, 73.990, 101.088),    # K(A) LYS105 NZ (Fab2 CH1)
]

# Cached template content to avoid re-reading from disk on every call.
_template_cache: str | None = None


def _load_antibody_template() -> str:
    """Read the 1HZH crystal structure and produce a PDB block with ADCDB chain IDs.

    Keeps only protein ATOM records (no HETATM, no solvent). Remaps chain IDs
    from 1HZH convention (H/K/L/M) to ADCDB convention (H/A/L/B).
    """
    global _template_cache
    if _template_cache is not None:
        return _template_cache

    if not _TEMPLATE_PDB.exists():
        raise FileNotFoundError(
            f"IgG1 template not found at {_TEMPLATE_PDB}. "
            "Download it: curl -o templates/1HZH.pdb https://files.rcsb.org/download/1HZH.pdb"
        )

    raw = _TEMPLATE_PDB.read_text()

    lines: list[str] = [
        "REMARK   1 PREDICTED ADC STRUCTURE",
        "REMARK   2 ANTIBODY TEMPLATE: PDB 1HZH (HUMAN IGG1 B12)",
        "REMARK   3 CHAINS H,A = HEAVY; L,B = LIGHT (REMAPPED FROM 1HZH H,K,L,M)",
        "REMARK   4 LINKER-PAYLOAD ATTACHED AS HETATM WITH CHAIN IDS D-M",
        "REMARK   5 THIS IS A MODELED/PREDICTED STRUCTURE, NOT EXPERIMENTAL",
    ]

    atom_serial = 1
    prev_chain = None

    for raw_line in raw.splitlines():
        # Keep only protein ATOM records
        if not raw_line.startswith("ATOM  "):
            continue

        # Parse chain ID (column 21, 0-indexed)
        orig_chain = raw_line[21]
        if orig_chain not in _CHAIN_MAP:
            continue

        new_chain = _CHAIN_MAP[orig_chain]

        # Insert TER between chains
        if prev_chain is not None and new_chain != prev_chain:
            lines.append("TER")
        prev_chain = new_chain

        # Renumber atom serial and remap chain ID
        line = f"ATOM  {atom_serial:5d}" + raw_line[11:21] + new_chain + raw_line[22:]
        lines.append(line)
        atom_serial += 1

    lines.append("TER")

    _template_cache = "\n".join(lines)
    return _template_cache


def _get_conjugation_sites(site_type: str | None, dar: float) -> list[tuple[float, float, float]]:
    """Get 3D positions for conjugation sites based on the 1HZH template."""
    n = max(1, int(round(dar)))
    if site_type == "lysine":
        sites = LYSINE_SITES
    else:
        sites = CYSTEINE_SITES
    return sites[:n]


def _offset_pdb_block(pdb_block: str, sx: float, sy: float, sz: float) -> str:
    """Offset HETATM coordinates in a PDB block to a conjugation site position."""
    offset_lines = []
    for line in pdb_block.splitlines():
        # Skip END/CONECT records from RDKit output — we add our own
        if line.startswith(("END", "CONECT")):
            continue
        if line.startswith("HETATM"):
            try:
                x = float(line[30:38]) + sx
                y = float(line[38:46]) + sy
                z = float(line[46:54]) + sz
                line = line[:30] + f"{x:8.3f}{y:8.3f}{z:8.3f}" + line[54:]
            except (ValueError, IndexError):
                pass
        offset_lines.append(line)
    return "\n".join(offset_lines)


def assemble_adc(
    linker_payload_smiles: str | None,
    conjugation_site: str | None,
    dar: float | None,
) -> str | None:
    """Assemble a complete ADC PDB file.

    Returns PDB content as string, or None on failure.
    """
    if not linker_payload_smiles:
        return None

    dar = dar or 4.0

    # Load antibody template from 1HZH crystal structure
    ab_pdb = _load_antibody_template()

    # Generate linker-payload conformer
    mol = generate_conformer(linker_payload_smiles)
    if mol is None:
        return None

    # Get conjugation sites
    sites = _get_conjugation_sites(conjugation_site, dar)

    # Build combined PDB
    parts = [ab_pdb]

    drug_chain_ids = "DEFGIJKM"
    for i, (sx, sy, sz) in enumerate(sites):
        if i >= len(drug_chain_ids):
            break
        pdb_block = mol_to_pdb_block(mol, chain_id=drug_chain_ids[i])
        if not pdb_block:
            continue
        parts.append(_offset_pdb_block(pdb_block, sx, sy, sz))
        parts.append("TER")

    parts.append("END")
    return "\n".join(parts)


def generate_and_save(
    adc_id: str,
    linker_payload_smiles: str | None,
    conjugation_site: str | None,
    dar: float | None,
    output_dir: str,
) -> str | None:
    """Generate ADC structure and save to file. Returns the file path or None."""
    pdb_content = assemble_adc(linker_payload_smiles, conjugation_site, dar)
    if pdb_content is None:
        return None

    out_path = Path(output_dir) / f"{adc_id}.pdb"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(pdb_content)
    return str(out_path)
