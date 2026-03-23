import { useState } from "react";
import { Link } from "react-router";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001/api/v1";
type Tab = "text" | "structure" | "sequence";

interface TextResults {
  adcs: { id: string; name: string; status: string }[];
  antibodies: { id: string; name: string }[];
  antigens: { id: string; name: string; gene_name: string | null }[];
  linkers: { id: string; name: string }[];
  payloads: { id: string; name: string }[];
}

interface SimResult {
  id: string;
  name: string;
  type?: string;
  chain?: string;
  similarity?: number;
  normalized_score?: number;
}

const tabLabels: Record<Tab, string> = {
  text: "Text Search",
  structure: "Structure Similarity",
  sequence: "Sequence Similarity",
};

const placeholders: Record<Tab, string> = {
  text: "Search ADCs, antibodies, antigens, payloads, linkers...",
  structure: "Enter SMILES (e.g., CC(=O)NC1=CC=C(O)C=C1)",
  sequence: "Enter amino acid sequence (e.g., EVQLVESGGGLVQPGG...)",
};

export default function Search() {
  const [tab, setTab] = useState<Tab>("text");
  const [query, setQuery] = useState("");
  const [textResults, setTextResults] = useState<TextResults | null>(null);
  const [simResults, setSimResults] = useState<SimResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setTextResults(null);
    setSimResults([]);
    setSearched(true);
    try {
      if (tab === "text") {
        const res = await fetch(`${API_BASE}/search?q=${encodeURIComponent(query)}`);
        setTextResults(await res.json());
      } else if (tab === "structure") {
        const res = await fetch(`${API_BASE}/search/structure?smiles=${encodeURIComponent(query)}`);
        setSimResults((await res.json()).results || []);
      } else {
        const res = await fetch(`${API_BASE}/search/sequence?sequence=${encodeURIComponent(query)}`);
        setSimResults((await res.json()).results || []);
      }
    } catch { /* silent */ }
    setLoading(false);
  }

  const hasTextResults = textResults && (
    textResults.adcs.length > 0 || textResults.antibodies.length > 0 ||
    textResults.antigens.length > 0 || textResults.linkers.length > 0 ||
    textResults.payloads.length > 0
  );

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Search</h1>

      <div className="flex gap-1 border-b border-border">
        {(Object.keys(tabLabels) as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => { setTab(t); setTextResults(null); setSimResults([]); setSearched(false); }}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              tab === t ? "border-primary text-primary" : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tabLabels[t]}
          </button>
        ))}
      </div>

      <form onSubmit={handleSearch} className="flex gap-2 max-w-2xl">
        {tab === "sequence" ? (
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholders[tab]}
            rows={3}
            className="flex-1 rounded-md border border-input px-3 py-2 text-sm bg-background font-mono"
          />
        ) : (
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={placeholders[tab]}
            className="flex-1 rounded-md border border-input px-3 py-2 text-sm bg-background font-mono"
          />
        )}
        <button
          type="submit"
          className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground self-start"
        >
          Search
        </button>
      </form>

      {loading && <p className="text-muted-foreground">Searching...</p>}

      {tab === "text" && textResults && (
        <div className="space-y-6">
          {textResults.adcs.length > 0 && <ResultSection title="ADCs">{textResults.adcs.map((r) => (
            <li key={r.id}><Link to={`/adc/${r.id}`} className="text-primary hover:underline">{r.name}</Link>
            <span className="text-muted-foreground text-sm ml-2 capitalize">{r.status.replace("_", " ")}</span></li>
          ))}</ResultSection>}
          {textResults.antibodies.length > 0 && <ResultSection title="Antibodies">{textResults.antibodies.map((r) => (
            <li key={r.id}><Link to={`/antibody/${r.id}`} className="text-primary hover:underline">{r.name}</Link></li>
          ))}</ResultSection>}
          {textResults.antigens.length > 0 && <ResultSection title="Antigens">{textResults.antigens.map((r) => (
            <li key={r.id}><Link to={`/antigen/${r.id}`} className="text-primary hover:underline">{r.name}</Link>
            {r.gene_name && <span className="text-muted-foreground text-sm ml-2">({r.gene_name})</span>}</li>
          ))}</ResultSection>}
          {textResults.linkers.length > 0 && <ResultSection title="Linkers">{textResults.linkers.map((r) => (
            <li key={r.id}><Link to={`/linker/${r.id}`} className="text-primary hover:underline">{r.name}</Link></li>
          ))}</ResultSection>}
          {textResults.payloads.length > 0 && <ResultSection title="Payloads">{textResults.payloads.map((r) => (
            <li key={r.id}><Link to={`/payload/${r.id}`} className="text-primary hover:underline">{r.name}</Link></li>
          ))}</ResultSection>}
          {!hasTextResults && <p className="text-muted-foreground">No results found.</p>}
        </div>
      )}

      {(tab === "structure" || tab === "sequence") && simResults.length > 0 && (
        <div className="rounded-lg border border-border overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b border-border bg-muted/50">
              <th className="text-left p-3 font-medium">Name</th>
              <th className="text-left p-3 font-medium">Type</th>
              <th className="text-right p-3 font-medium">{tab === "structure" ? "Tanimoto" : "Score"}</th>
            </tr></thead>
            <tbody>{simResults.map((r) => (
              <tr key={r.id} className="border-b border-border hover:bg-muted/30">
                <td className="p-3"><Link to={`/${r.type || (tab === "sequence" ? "antibody" : "payload")}/${r.id}`} className="text-primary hover:underline">{r.name}</Link></td>
                <td className="p-3 capitalize">{r.type || r.chain || "-"}</td>
                <td className="p-3 text-right font-mono">{(tab === "structure" ? r.similarity : r.normalized_score)?.toFixed(3)}</td>
              </tr>
            ))}</tbody>
          </table>
        </div>
      )}
      {(tab === "structure" || tab === "sequence") && searched && !loading && simResults.length === 0 && (
        <p className="text-muted-foreground">No results found.</p>
      )}
    </div>
  );
}

function ResultSection({ title, children }: { title: string; children: React.ReactNode }) {
  return <div><h2 className="font-semibold mb-2">{title}</h2><ul className="space-y-1">{children}</ul></div>;
}
