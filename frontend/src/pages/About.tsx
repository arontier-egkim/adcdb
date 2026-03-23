export default function About() {
  return (
    <div className="max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">About ADCDB</h1>
      <p className="text-muted-foreground">
        ADCDB is a database for Antibody-Drug Conjugates (ADCs) with predicted
        3D structures. It provides comprehensive data on ADCs, their antibodies,
        antigens, linkers, payloads, and clinical/preclinical activity.
      </p>
      <div className="space-y-3">
        <h2 className="font-semibold">Data Sources</h2>
        <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1">
          <li>Published ADC literature and FDA approval documents</li>
          <li>ChEMBL for payload/linker structures (SMILES)</li>
          <li>UniProt for antibody sequences and antigen info</li>
          <li>ClinicalTrials.gov for trial data (NCT numbers)</li>
          <li>AlphaFold DB for antibody structures</li>
        </ul>
      </div>
      <div className="space-y-3">
        <h2 className="font-semibold">3D Structures</h2>
        <p className="text-sm text-muted-foreground">
          3D structures are predicted/modeled using template-based IgG assembly
          with RDKit conformer generation for the linker-payload unit. These
          represent approximate spatial arrangements and should not be used for
          quantitative structural analysis.
        </p>
      </div>
    </div>
  );
}
