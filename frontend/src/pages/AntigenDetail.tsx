import { useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import { apiFetch, type Antigen, type ADCListItem } from "@/lib/api";

export default function AntigenDetail() {
  const { id } = useParams<{ id: string }>();
  const [ag, setAg] = useState<Antigen | null>(null);
  const [adcs, setAdcs] = useState<ADCListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!id) return;
    Promise.all([
      apiFetch<Antigen>(`/antigens/${id}`),
      apiFetch<ADCListItem[]>(`/antigens/${id}/adcs`),
    ])
      .then(([a, d]) => { setAg(a); setAdcs(d); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-muted-foreground">Loading...</p>;
  if (!ag) return <p className="text-destructive">Antigen not found.</p>;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">{ag.name}</h1>
      <div className="rounded-lg border border-border p-4">
        <dl className="grid grid-cols-2 gap-2 text-sm max-w-md">
          <dt className="text-muted-foreground">Gene Name</dt><dd>{ag.gene_name || "-"}</dd>
          <dt className="text-muted-foreground">UniProt</dt><dd>{ag.uniprot_id || "-"}</dd>
          <dt className="text-muted-foreground">Description</dt><dd>{ag.description || "-"}</dd>
        </dl>
      </div>
      {adcs.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold">ADCs targeting this antigen ({adcs.length})</h2>
          <ul className="space-y-1">{adcs.map((a) => (
            <li key={a.id}><Link to={`/adc/${a.id}`} className="text-primary hover:underline">{a.name}</Link>
            <span className="text-muted-foreground text-sm ml-2 capitalize">{a.status.replace("_", " ")}</span></li>
          ))}</ul>
        </div>
      )}
    </div>
  );
}
