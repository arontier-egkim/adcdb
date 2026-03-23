const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001/api/v1";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    throw new Error(`API error: ${res.status} ${res.statusText}`);
  }
  return res.json();
}

export interface Antigen {
  id: string;
  name: string;
  synonyms: string[] | null;
  gene_name: string | null;
  uniprot_id: string | null;
  description: string | null;
}

export interface Antibody {
  id: string;
  name: string;
  synonyms: string[] | null;
  isotype: string | null;
  origin: string | null;
  antigen_id: string;
  antigen: Antigen;
  heavy_chain_seq: string | null;
  light_chain_seq: string | null;
  uniprot_id: string | null;
}

export interface Linker {
  id: string;
  name: string;
  cleavable: boolean;
  cleavage_mechanism: string | null;
  coupling_chemistry: string | null;
  smiles: string | null;
  inchi: string | null;
  inchikey: string | null;
  formula: string | null;
  iupac_name: string | null;
  mol_weight: number | null;
}

export interface Payload {
  id: string;
  name: string;
  synonyms: string[] | null;
  target: string | null;
  moa: string | null;
  bystander_effect: boolean | null;
  smiles: string | null;
  inchi: string | null;
  inchikey: string | null;
  formula: string | null;
  iupac_name: string | null;
  mol_weight: number | null;
}

export interface Activity {
  id: string;
  adc_id: string;
  activity_type: string;
  nct_number: string | null;
  phase: string | null;
  orr: number | null;
  model: string | null;
  tgi: number | null;
  ic50_value: number | null;
  ic50_unit: string | null;
  cell_line: string | null;
  notes: string | null;
}

export interface ADC {
  id: string;
  name: string;
  brand_name: string | null;
  synonyms: string[] | null;
  organization: string | null;
  status: string;
  dar: number | null;
  conjugation_site: string | null;
  indications: string[] | null;
  antibody_id: string;
  linker_id: string;
  payload_id: string;
  linker_payload_smiles: string | null;
  antibody: Antibody;
  linker: Linker;
  payload: Payload;
  activities: Activity[];
  structure_3d_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface ADCListItem {
  id: string;
  name: string;
  brand_name: string | null;
  status: string;
  dar: number | null;
  organization: string | null;
  antibody_name: string;
  antigen_name: string;
  linker_name: string;
  payload_name: string;
}

export interface Stats {
  total_adcs: number;
  top_antigens: { name: string; count: number }[];
  top_payload_targets: { name: string; count: number }[];
  pipeline: Record<string, number>;
}
