import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router";
import { apiFetch, type ADCListItem } from "@/lib/api";

const statuses = ["approved", "phase_3", "phase_2", "phase_1", "investigative"];

export default function Browse() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [adcs, setAdcs] = useState<ADCListItem[]>([]);
  const [loading, setLoading] = useState(true);
  const status = searchParams.get("status") || "";

  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams();
    if (status) params.set("status", status);
    apiFetch<ADCListItem[]>(`/adcs?${params.toString()}`)
      .then(setAdcs)
      .catch(() => setAdcs([]))
      .finally(() => setLoading(false));
  }, [status]);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Browse ADCs</h1>

      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setSearchParams({})}
          className={`rounded-md border border-border px-3 py-1 text-sm ${
            !status ? "bg-primary text-primary-foreground" : ""
          }`}
        >
          All
        </button>
        {statuses.map((s) => (
          <button
            key={s}
            onClick={() => setSearchParams({ status: s })}
            className={`rounded-md border border-border px-3 py-1 text-sm capitalize ${
              status === s ? "bg-primary text-primary-foreground" : ""
            }`}
          >
            {s.replace("_", " ")}
          </button>
        ))}
      </div>

      {loading ? (
        <p className="text-muted-foreground">Loading...</p>
      ) : (
        <div className="rounded-lg border border-border overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border bg-muted/50">
                <th className="text-left p-3 font-medium">Name</th>
                <th className="text-left p-3 font-medium">Status</th>
                <th className="text-left p-3 font-medium">Antibody</th>
                <th className="text-left p-3 font-medium">Antigen</th>
                <th className="text-left p-3 font-medium">Payload</th>
                <th className="text-left p-3 font-medium">Linker</th>
                <th className="text-right p-3 font-medium">DAR</th>
              </tr>
            </thead>
            <tbody>
              {adcs.map((adc) => (
                <tr key={adc.id} className="border-b border-border hover:bg-muted/30">
                  <td className="p-3">
                    <Link to={`/adc/${adc.id}`} className="text-primary hover:underline font-medium">
                      {adc.name}
                    </Link>
                  </td>
                  <td className="p-3 capitalize">{adc.status.replace("_", " ")}</td>
                  <td className="p-3">{adc.antibody_name}</td>
                  <td className="p-3">{adc.antigen_name}</td>
                  <td className="p-3">{adc.payload_name}</td>
                  <td className="p-3">{adc.linker_name}</td>
                  <td className="p-3 text-right">{adc.dar ?? "-"}</td>
                </tr>
              ))}
              {adcs.length === 0 && (
                <tr>
                  <td colSpan={7} className="p-6 text-center text-muted-foreground">
                    No ADCs found.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
