"""Assemble ADC 3D structure: antibody template + linker-payload conformers."""

import math
from pathlib import Path

from app.structure.conformer import generate_conformer, mol_to_pdb_block


# Approximate IgG1 interchain disulfide Cys positions (Angstroms)
# These are typical positions for DAR=4 cysteine conjugation on IgG1
CYSTEINE_SITES = [
    (25.0, 10.0, 5.0),
    (-25.0, 10.0, 5.0),
    (25.0, -10.0, 5.0),
    (-25.0, -10.0, 5.0),
    (15.0, 25.0, 0.0),
    (-15.0, 25.0, 0.0),
    (15.0, -25.0, 0.0),
    (-15.0, -25.0, 0.0),
]

# Approximate surface Lys positions
LYSINE_SITES = [
    (20.0, 15.0, 10.0),
    (-20.0, 15.0, 10.0),
    (10.0, -20.0, 15.0),
    (-10.0, -20.0, 15.0),
    (0.0, 25.0, 5.0),
    (0.0, -25.0, 5.0),
    (15.0, 0.0, 20.0),
    (-15.0, 0.0, 20.0),
]


def _get_conjugation_sites(site_type: str | None, dar: float) -> list[tuple[float, float, float]]:
    """Get approximate 3D positions for conjugation sites."""
    n = max(1, int(round(dar)))
    if site_type == "lysine":
        sites = LYSINE_SITES
    else:
        sites = CYSTEINE_SITES
    return sites[:n]


def _generate_antibody_template() -> str:
    """Generate a minimal IgG-shaped PDB with CA atoms tracing the Y-shape.

    This is a simplified representation — not a real crystal structure, but
    enough to show the topology in Mol*.
    """
    lines = ["REMARK   PREDICTED IgG TEMPLATE - APPROXIMATE TOPOLOGY"]
    atom_idx = 1

    def add_atom(x, y, z, chain, resname="ALA", resseq=1):
        nonlocal atom_idx
        line = (
            f"ATOM  {atom_idx:5d}  CA  {resname} {chain}{resseq:4d}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00  0.00           C"
        )
        lines.append(line)
        atom_idx += 1

    # Heavy chain 1 (H) - right arm of Y
    for i in range(50):
        t = i / 49.0
        if t < 0.4:
            # Fc stem
            x = 2.0
            y = -30.0 + t * 75.0
            z = 0.0
        else:
            # Fab arm going right
            x = 2.0 + (t - 0.4) * 60.0
            y = 0.0 + (t - 0.4) * 50.0
            z = math.sin(t * 3.14) * 5.0
        add_atom(x, y, z, "H", resseq=i + 1)

    # Heavy chain 2 (h) - left arm of Y
    for i in range(50):
        t = i / 49.0
        if t < 0.4:
            x = -2.0
            y = -30.0 + t * 75.0
            z = 0.0
        else:
            x = -2.0 - (t - 0.4) * 60.0
            y = 0.0 + (t - 0.4) * 50.0
            z = math.sin(t * 3.14) * 5.0
        add_atom(x, y, z, "A", resseq=i + 1)

    # Light chain 1 (L)
    for i in range(30):
        t = i / 29.0
        x = 15.0 + t * 20.0
        y = 10.0 + t * 20.0
        z = 5.0 + math.sin(t * 3.14) * 3.0
        add_atom(x, y, z, "L", resseq=i + 1)

    # Light chain 2 (l)
    for i in range(30):
        t = i / 29.0
        x = -15.0 - t * 20.0
        y = 10.0 + t * 20.0
        z = 5.0 + math.sin(t * 3.14) * 3.0
        add_atom(x, y, z, "B", resseq=i + 1)

    lines.append("TER")
    return "\n".join(lines)


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

    # Generate antibody template
    ab_pdb = _generate_antibody_template()

    # Generate linker-payload conformer
    mol = generate_conformer(linker_payload_smiles)
    if mol is None:
        return None

    # Get conjugation sites
    sites = _get_conjugation_sites(conjugation_site, dar)

    # Build combined PDB
    parts = [ab_pdb]

    chain_ids = "DEFGIJKM"
    for i, (sx, sy, sz) in enumerate(sites):
        if i >= len(chain_ids):
            break
        # Generate a PDB block for this copy and offset it to the site
        pdb_block = mol_to_pdb_block(mol, chain_id=chain_ids[i])
        if not pdb_block:
            continue

        # Offset all HETATM coordinates to the conjugation site
        offset_lines = []
        for line in pdb_block.splitlines():
            if line.startswith("HETATM"):
                try:
                    x = float(line[30:38]) + sx
                    y = float(line[38:46]) + sy
                    z = float(line[46:54]) + sz
                    line = line[:30] + f"{x:8.3f}{y:8.3f}{z:8.3f}" + line[54:]
                except (ValueError, IndexError):
                    pass
            offset_lines.append(line)
        parts.append("\n".join(offset_lines))
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
