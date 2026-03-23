import { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import { apiFetch, type Antibody, type ADCListItem } from "@/lib/api";

export default function AntibodyDetail() {
  const { id } = useParams<{ id: string }>();
  const [ab, setAb] = useState<Antibody | null>(null);
  const [adcs, setAdcs] = useState<ADCListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      apiFetch<Antibody>(`/antibodies/${id}`),
      apiFetch<ADCListItem[]>(`/antibodies/${id}/adcs`),
    ])
      .then(([a, d]) => { setAb(a); setAdcs(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-muted-foreground">Loading...</p>;
  if (!ab) return <p className="text-destructive">Antibody not found.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{ab.name}</h1>
      <div className="rounded-lg border border-border p-4">
        <dl className="grid grid-cols-2 gap-2 text-sm max-w-md">
          <dt className="text-muted-foreground">Isotype</dt><dd>{ab.isotype || "-"}</dd>
          <dt className="text-muted-foreground">Origin</dt><dd className="capitalize">{ab.origin || "-"}</dd>
          <dt className="text-muted-foreground">Target Antigen</dt>
          <dd><Link to={`/antigen/${ab.antigen.id}`} className="text-primary hover:underline">{ab.antigen.name}</Link></dd>
          <dt className="text-muted-foreground">UniProt</dt><dd>{ab.uniprot_id || "-"}</dd>
        </dl>
      </div>
      {ab.heavy_chain_seq && (
        <div className="space-y-2">
          <h2 className="font-semibold">Heavy Chain Sequence</h2>
          <pre className="rounded-lg border border-border p-3 text-xs overflow-x-auto break-all whitespace-pre-wrap">{ab.heavy_chain_seq}</pre>
        </div>
      )}
      {adcs.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold">ADCs using this antibody ({adcs.length})</h2>
          <ul className="space-y-1">{adcs.map((a) => (
            <li key={a.id}><Link to={`/adc/${a.id}`} className="text-primary hover:underline">{a.name}</Link>
            <span className="text-muted-foreground text-sm ml-2 capitalize">{a.status.replace("_", " ")}</span></li>
          ))}</ul>
        </div>
      )}
    </div>
  );
}
