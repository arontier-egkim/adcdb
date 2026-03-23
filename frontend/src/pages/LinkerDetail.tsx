import { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import { apiFetch, type Linker, type ADCListItem } from "@/lib/api";

export default function LinkerDetail() {
  const { id } = useParams<{ id: string }>();
  const [linker, setLinker] = useState<Linker | null>(null);
  const [adcs, setAdcs] = useState<ADCListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      apiFetch<Linker>(`/linkers/${id}`),
      apiFetch<ADCListItem[]>(`/linkers/${id}/adcs`),
    ])
      .then(([l, d]) => { setLinker(l); setAdcs(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-muted-foreground">Loading...</p>;
  if (!linker) return <p className="text-destructive">Linker not found.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{linker.name}</h1>
      <div className="rounded-lg border border-border p-4">
        <dl className="grid grid-cols-2 gap-2 text-sm max-w-md">
          <dt className="text-muted-foreground">Cleavable</dt><dd>{linker.cleavable ? "Yes" : "No"}</dd>
          <dt className="text-muted-foreground">Cleavage Mechanism</dt><dd>{linker.cleavage_mechanism || "-"}</dd>
          <dt className="text-muted-foreground">Coupling Chemistry</dt><dd>{linker.coupling_chemistry || "-"}</dd>
          <dt className="text-muted-foreground">Formula</dt><dd>{linker.formula || "-"}</dd>
          <dt className="text-muted-foreground">Mol. Weight</dt><dd>{linker.mol_weight ? `${linker.mol_weight} Da` : "-"}</dd>
          <dt className="text-muted-foreground">SMILES</dt><dd className="break-all text-xs">{linker.smiles || "-"}</dd>
        </dl>
      </div>
      {adcs.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold">ADCs using this linker ({adcs.length})</h2>
          <ul className="space-y-1">{adcs.map((a) => (
            <li key={a.id}><Link to={`/adc/${a.id}`} className="text-primary hover:underline">{a.name}</Link></li>
          ))}</ul>
        </div>
      )}
    </div>
  );
}
