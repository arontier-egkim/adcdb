import { useEffect, useState } from "react";
import { Link } from "react-router";
import { apiFetch, type Stats } from "@/lib/api";

export default function Home() {
  const [stats, setStats] = useState<Stats | null>(null);

  useEffect(() => {
    apiFetch<Stats>("/stats").then(setStats).catch(() => {});
  }, []);

  return (
    <div className="space-y-8">
      <section className="text-center py-12">
        <h1 className="text-4xl font-bold text-primary mb-3">ADCDB</h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Antibody-Drug Conjugate Database with predicted 3D structures.
          Browse, search, and visualize ADCs, their components, and activity data.
        </p>
        <div className="mt-6 flex gap-3 justify-center">
          <Link
            to="/browse"
            className="inline-flex items-center rounded-md bg-primary px-6 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Browse ADCs
          </Link>
          <Link
            to="/search"
            className="inline-flex items-center rounded-md border border-border px-6 py-2 text-sm font-medium hover:bg-accent"
          >
            Search
          </Link>
        </div>
      </section>

      {stats && (
        <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="rounded-lg border border-border p-6">
            <h3 className="text-sm font-medium text-muted-foreground">Total ADCs</h3>
            <p className="text-3xl font-bold text-primary">{stats.total_adcs}</p>
          </div>
          <div className="rounded-lg border border-border p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Top Antigens</h3>
            <ul className="space-y-1">
              {stats.top_antigens.map((a) => (
                <li key={a.name} className="flex justify-between text-sm">
                  <span>{a.name}</span>
                  <span className="text-muted-foreground">{a.count}</span>
                </li>
              ))}
              {stats.top_antigens.length === 0 && (
                <li className="text-sm text-muted-foreground">No data yet</li>
              )}
            </ul>
          </div>
          <div className="rounded-lg border border-border p-6">
            <h3 className="text-sm font-medium text-muted-foreground mb-3">Pipeline</h3>
            <ul className="space-y-1">
              {Object.entries(stats.pipeline).map(([status, count]) => (
                <li key={status} className="flex justify-between text-sm">
                  <span className="capitalize">{status.replace("_", " ")}</span>
                  <span className="text-muted-foreground">{count}</span>
                </li>
              ))}
              {Object.keys(stats.pipeline).length === 0 && (
                <li className="text-sm text-muted-foreground">No data yet</li>
              )}
            </ul>
          </div>
        </section>
      )}
    </div>
  );
}
