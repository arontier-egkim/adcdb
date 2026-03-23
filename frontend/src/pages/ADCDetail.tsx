import { Suspense, lazy, useEffect, useState } from "react";
import { useParams, Link } from "react-router";
import { apiFetch, type ADC } from "@/lib/api";

const MolViewer = lazy(() => import("@/components/MolViewer"));

export default function ADCDetail() {
  const { id } = useParams<{ id: string }>();
  const [adc, setAdc] = useState<ADC | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;
    setLoading(true);
    apiFetch<ADC>(`/adcs/${id}`)
      .then(setAdc)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <p className="text-muted-foreground">Loading...</p>;
  if (error || !adc) return <p className="text-destructive">ADC not found.</p>;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold">{adc.name}</h1>
        {adc.brand_name && <p className="text-muted-foreground">{adc.brand_name}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="rounded-lg border border-border p-4 space-y-3">
          <h2 className="font-semibold">General</h2>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-muted-foreground">Status</dt>
            <dd className="capitalize">{adc.status.replace("_", " ")}</dd>
            <dt className="text-muted-foreground">Organization</dt>
            <dd>{adc.organization || "-"}</dd>
            <dt className="text-muted-foreground">DAR</dt>
            <dd>{adc.dar ?? "-"}</dd>
            <dt className="text-muted-foreground">Conjugation Site</dt>
            <dd className="capitalize">{adc.conjugation_site?.replace("_", " ") || "-"}</dd>
            <dt className="text-muted-foreground">Indications</dt>
            <dd>{adc.indications?.join(", ") || "-"}</dd>
          </dl>
        </div>

        <div className="rounded-lg border border-border p-4 space-y-3">
          <h2 className="font-semibold">Components</h2>
          <dl className="grid grid-cols-2 gap-2 text-sm">
            <dt className="text-muted-foreground">Antibody</dt>
            <dd><Link to={`/antibody/${adc.antibody.id}`} className="text-primary hover:underline">{adc.antibody.name}</Link></dd>
            <dt className="text-muted-foreground">Antigen</dt>
            <dd><Link to={`/antigen/${adc.antibody.antigen.id}`} className="text-primary hover:underline">{adc.antibody.antigen.name}</Link></dd>
            <dt className="text-muted-foreground">Linker</dt>
            <dd><Link to={`/linker/${adc.linker.id}`} className="text-primary hover:underline">{adc.linker.name}</Link></dd>
            <dt className="text-muted-foreground">Payload</dt>
            <dd><Link to={`/payload/${adc.payload.id}`} className="text-primary hover:underline">{adc.payload.name}</Link></dd>
          </dl>
        </div>
      </div>

      {adc.structure_3d_path ? (
        <Suspense fallback={<div className="rounded-lg border border-border p-6 text-center text-muted-foreground h-[500px] flex items-center justify-center">Loading 3D viewer...</div>}>
          <MolViewer adcId={adc.id} />
        </Suspense>
      ) : (
        <div className="rounded-lg border border-border p-6 text-center text-muted-foreground">
          Predicted 3D structure not yet available for this ADC.
        </div>
      )}

      {adc.activities.length > 0 && (
        <div className="space-y-3">
          <h2 className="font-semibold text-lg">Activity Data</h2>
          <div className="rounded-lg border border-border overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left p-3 font-medium">Type</th>
                  <th className="text-left p-3 font-medium">Phase</th>
                  <th className="text-left p-3 font-medium">NCT</th>
                  <th className="text-right p-3 font-medium">ORR (%)</th>
                  <th className="text-left p-3 font-medium">Cell Line</th>
                  <th className="text-right p-3 font-medium">IC50</th>
                  <th className="text-right p-3 font-medium">TGI (%)</th>
                </tr>
              </thead>
              <tbody>
                {adc.activities.map((a) => (
                  <tr key={a.id} className="border-b border-border">
                    <td className="p-3 capitalize">{a.activity_type.replace("_", " ")}</td>
                    <td className="p-3">{a.phase || "-"}</td>
                    <td className="p-3">{a.nct_number || "-"}</td>
                    <td className="p-3 text-right">{a.orr ?? "-"}</td>
                    <td className="p-3">{a.cell_line || "-"}</td>
                    <td className="p-3 text-right">{a.ic50_value != null ? `${a.ic50_value} ${a.ic50_unit || ""}` : "-"}</td>
                    <td className="p-3 text-right">{a.tgi ?? "-"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
