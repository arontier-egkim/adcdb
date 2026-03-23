import { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import { apiFetch, type Payload, type ADCListItem } from "@/lib/api";
import MoleculeDrawing from "@/components/MoleculeDrawing";

export default function PayloadDetail() {
  const { id } = useParams<{ id: string }>();
  const [payload, setPayload] = useState<Payload | null>(null);
  const [adcs, setAdcs] = useState<ADCListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      apiFetch<Payload>(`/payloads/${id}`),
      apiFetch<ADCListItem[]>(`/payloads/${id}/adcs`),
    ])
      .then(([p, d]) => { setPayload(p); setAdcs(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-muted-foreground">Loading...</p>;
  if (!payload) return <p className="text-destructive">Payload not found.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{payload.name}</h1>
      <div className="rounded-lg border border-border p-4">
        <dl className="grid grid-cols-2 gap-2 text-sm max-w-md">
          <dt className="text-muted-foreground">Target</dt><dd>{payload.target || "-"}</dd>
          <dt className="text-muted-foreground">MOA</dt><dd>{payload.moa || "-"}</dd>
          <dt className="text-muted-foreground">Bystander Effect</dt>
          <dd>{payload.bystander_effect == null ? "-" : payload.bystander_effect ? "Yes" : "No"}</dd>
          <dt className="text-muted-foreground">Formula</dt><dd>{payload.formula || "-"}</dd>
          <dt className="text-muted-foreground">Mol. Weight</dt><dd>{payload.mol_weight ? `${payload.mol_weight} Da` : "-"}</dd>
          <dt className="text-muted-foreground">SMILES</dt><dd className="text-xs font-mono break-all">{payload.smiles || "-"}</dd>
        </dl>
      </div>
      {payload.smiles && payload.smiles !== "C" && <MoleculeDrawing smiles={payload.smiles} />}
      {adcs.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold">ADCs using this payload ({adcs.length})</h2>
          <ul className="space-y-1">{adcs.map((a) => (
            <li key={a.id}><Link to={`/adc/${a.id}`} className="text-primary hover:underline">{a.name}</Link></li>
          ))}</ul>
        </div>
      )}
    </div>
  );
}
