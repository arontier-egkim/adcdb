import { MoleculeRepresentation } from "@iktos-oss/molecule-representation";

function cleanSmiles(smiles: string): string {
  return smiles.replace(/\[\*:\d+\]/g, "[H]");
}

// ACS1996 drawing options passed via the `details` prop to RDKit MolDrawOptions
const ACS1996_DETAILS: Record<string, unknown> = {
  bondLineWidth: 1.2,
  minFontSize: 10,
  annotationFontScale: 0.75,
  additionalAtomLabelPadding: 0.05,
  multipleBondOffset: 0.15,
  scaleBondWidth: true,
  fixedBondLength: 25,
};

export default function MoleculeDrawing({
  smiles,
  width = 400,
  height = 300,
}: {
  smiles: string;
  width?: number;
  height?: number;
}) {
  const cleaned = cleanSmiles(smiles);

  return (
    <div className="rounded-lg border border-border bg-white p-4 flex items-center justify-center">
      <MoleculeRepresentation
        smiles={cleaned}
        width={width}
        height={height}
        details={ACS1996_DETAILS}
      />
    </div>
  );
}
