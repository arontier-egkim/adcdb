import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import { DefaultPluginUISpec } from "molstar/lib/mol-plugin-ui/spec";
import { createPluginUI } from "molstar/lib/mol-plugin-ui";
import "molstar/lib/mol-plugin-ui/skin/light.scss";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001/api/v1";

export default function MolViewer({ adcId }: { adcId: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pluginRef = useRef<PluginUIContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      if (!containerRef.current) return;

      try {
        // Fetch PDB first to fail fast
        const res = await fetch(`${API_BASE}/adcs/${adcId}/structure`);
        if (!res.ok) {
          setError("Structure not available");
          setLoading(false);
          return;
        }
        const pdbData = await res.text();
        if (cancelled) return;

        // Create Mol* plugin with React 18 render
        const plugin = await createPluginUI({
          target: containerRef.current,
          spec: {
            ...DefaultPluginUISpec(),
            layout: {
              initial: {
                isExpanded: false,
                showControls: false,
              },
            },
          },
          render: (component, element) => {
            createRoot(element!).render(component);
          },
        });

        if (cancelled) {
          plugin.dispose();
          return;
        }
        pluginRef.current = plugin;

        // Load PDB data
        const data = await plugin.builders.data.rawData({
          data: pdbData,
          label: "ADC Structure",
        });
        const trajectory = await plugin.builders.structure.parseTrajectory(
          data,
          "pdb"
        );
        await plugin.builders.structure.hierarchy.applyPreset(
          trajectory,
          "default"
        );

        if (!cancelled) setLoading(false);
      } catch (e: unknown) {
        console.error("Mol* error:", e);
        if (!cancelled) {
          const msg = e instanceof Error ? e.message : "Unknown error";
          setError("Failed to load 3D viewer: " + msg);
          setLoading(false);
        }
      }
    }

    init();

    return () => {
      cancelled = true;
      if (pluginRef.current) {
        pluginRef.current.dispose();
        pluginRef.current = null;
      }
    };
  }, [adcId]);

  if (error) {
    return (
      <div className="rounded-lg border border-border p-6 text-center space-y-3">
        <p className="text-muted-foreground">{error}</p>
        <a
          href={`${API_BASE}/adcs/${adcId}/structure`}
          download={`${adcId}.pdb`}
          className="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground"
        >
          Download PDB File
        </a>
        <p className="text-xs text-muted-foreground">
          Open in PyMOL, ChimeraX, or{" "}
          <a
            href="https://molstar.org/viewer/"
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary hover:underline"
          >
            Mol* Viewer online
          </a>
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold text-lg">3D Structure</h2>
        <div className="flex items-center gap-3">
          <a
            href={`${API_BASE}/adcs/${adcId}/structure`}
            download={`${adcId}.pdb`}
            className="text-xs text-primary hover:underline"
          >
            Download PDB
          </a>
          <span className="text-xs text-muted-foreground">
            Predicted/modeled structure
          </span>
        </div>
      </div>
      <div
        className="rounded-lg border border-border overflow-hidden relative"
        style={{ height: 500 }}
      >
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <p className="text-muted-foreground">Loading 3D viewer...</p>
          </div>
        )}
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      </div>
    </div>
  );
}
