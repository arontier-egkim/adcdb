import { MoleculeRepresentation } from "@iktos-oss/molecule-representation";

function cleanSmiles(smiles: string): string {
  return smiles.replace(/\[\*:\d+\]/g, "[H]");
}

// ACS1996 drawing options — values from RDKit's rdMolDraw2D.SetACS1996Mode()
const ACS1996_DETAILS: Record<string, unknown> = {
  bondLineWidth: 0.6,
  scaleBondWidth: false,
  fixedBondLength: 14.4,  // 2x ACS1996 default (7.2) for larger molecule rendering
  additionalAtomLabelPadding: 0.066,
  multipleBondOffset: 0.18,
  annotationFontScale: 0.5,
  minFontSize: 6,
  maxFontSize: 40,
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
    <div className="rounded-lg border border-border bg-white p-4 flex items-center justify-center overflow-hidden">
      <MoleculeRepresentation
        smiles={cleaned}
        width={width}
        height={height}
        details={ACS1996_DETAILS}
        zoomable
      />
    </div>
  );
}
