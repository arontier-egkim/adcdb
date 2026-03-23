"""Generate 3D conformers for linker-payload molecules using RDKit."""

from rdkit import Chem
from rdkit.Chem import AllChem


def generate_conformer(linker_payload_smiles: str) -> Chem.Mol | None:
    """Generate a 3D conformer from linker-payload SMILES.

    The SMILES should have [*:1] marking the antibody attachment point.
    We replace it with [H] for conformer generation and record the atom index.

    Returns the 3D molecule or None on failure.
    """
    if not linker_payload_smiles:
        return None

    # Record attachment point before replacing
    clean_smiles = linker_payload_smiles.replace("[*:1]", "[H]")
    mol = Chem.MolFromSmiles(clean_smiles)
    if mol is None:
        return None

    mol = Chem.AddHs(mol)

    # Embed with ETKDGv3
    params = AllChem.ETKDGv3()
    params.randomSeed = 42
    result = AllChem.EmbedMolecule(mol, params)
    if result != 0:
        # Fallback: try with random coords
        params.useRandomCoords = True
        result = AllChem.EmbedMolecule(mol, params)
        if result != 0:
            return None

    # Minimize with MMFF94
    try:
        AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
    except Exception:
        # UFF fallback
        try:
            AllChem.UFFOptimizeMolecule(mol, maxIters=500)
        except Exception:
            pass  # Use unoptimized geometry

    return mol


def mol_to_pdb_block(mol: Chem.Mol, chain_id: str = "D") -> str:
    """Convert RDKit mol to PDB block with specified chain ID."""
    pdb = Chem.MolToPDBBlock(mol)
    if not pdb:
        return ""

    lines = []
    atom_serial = 1
    for line in pdb.splitlines():
        if line.startswith(("HETATM", "ATOM")):
            # Replace chain ID (column 22)
            line = line[:21] + chain_id + line[22:]
            # Renumber
            line = f"HETATM{atom_serial:5d}" + line[11:]
            atom_serial += 1
        lines.append(line)
    return "\n".join(lines)
