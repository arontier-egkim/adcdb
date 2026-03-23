import { useEffect, useRef, useState, useCallback } from "react";
import { createRoot } from "react-dom/client";
import { PluginUIContext } from "molstar/lib/mol-plugin-ui/context";
import { DefaultPluginUISpec } from "molstar/lib/mol-plugin-ui/spec";
import { createPluginUI } from "molstar/lib/mol-plugin-ui";
import "molstar/lib/mol-plugin-ui/skin/light.scss";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8001/api/v1";

type Preset = "rainbow" | "surface" | "interactions";

async function applyPreset(plugin: PluginUIContext, preset: Preset, skipClear = false) {
  const structures = plugin.managers.structure.hierarchy.current.structures;
  if (!structures.length) return;

  const struct = structures[0];
  const structureRef = struct.cell.transform.ref;

  // Clear existing representations (skip on initial load)
  if (!skipClear) {
    await plugin.dataTransaction(async () => {
      const update = plugin.state.data.build();
      for (const comp of struct.components || []) {
        update.delete(comp.cell.transform.ref);
      }
      await update.commit();
    });
  }

  if (preset === "rainbow") {
    await plugin.builders.structure.representation.applyPreset(
      structureRef,
      "polymer-and-ligand",
      { theme: { globalName: "chain-id" as const } }
    );
  } else if (preset === "surface") {
    await plugin.builders.structure.representation.applyPreset(
      structureRef,
      "molecular-surface",
      { theme: { globalName: "chain-id" as const } }
    );
  } else if (preset === "interactions") {
    // Show ligands as ball-and-stick + surrounding residues + interactions + labels
    const ligand = await plugin.builders.structure.tryCreateComponentStatic(
      structureRef,
      "ligand"
    );
    if (ligand) {
      await plugin.builders.structure.representation.addRepresentation(
        ligand,
        { type: "ball-and-stick", color: "element-symbol" }
      );
    }
    // Show protein residues near the ligand (interaction environment)
    const surroundings = await plugin.builders.structure.tryCreateComponentFromExpression(
      structureRef,
      // @ts-expect-error -- Mol* internal expression types
      (await import("molstar/lib/mol-script/language/expression")).MolScriptBuilder.struct.modifier.includeSurroundings({
        0: (await import("molstar/lib/mol-script/language/expression")).MolScriptBuilder.struct.generator.atomGroups({
          "entity-test": (await import("molstar/lib/mol-script/language/expression")).MolScriptBuilder.core.rel.eq([
            (await import("molstar/lib/mol-script/language/expression")).MolScriptBuilder.ammp("entityType"),
            "non-polymer"
          ])
        }),
        radius: 5,
        "as-whole-residues": true,
      }),
      "surroundings",
      { label: "Interaction Environment" }
    );
    if (surroundings) {
      await plugin.builders.structure.representation.addRepresentation(
        surroundings,
        { type: "ball-and-stick", color: "element-symbol", typeParams: { sizeFactor: 0.2 } }
      );
      // Add residue labels (3-letter code + number)
      await plugin.builders.structure.representation.addRepresentation(
        surroundings,
        {
          type: "label" as never,
          typeParams: {
            level: "residue" as never,
            granularity: "residue" as never,
          } as never,
          color: "uniform" as never,
          colorParams: { value: 0x333333 } as never,
        }
      );
    }
    // Add interaction lines on everything
    const allComp = await plugin.builders.structure.tryCreateComponentStatic(
      structureRef,
      "all"
    );
    if (allComp) {
      await plugin.builders.structure.representation.addRepresentation(
        allComp,
        {
          type: "interactions" as never,
          color: "interaction-type" as never,
        }
      );
    }
  }
}

export default function MolViewer({ adcId }: { adcId: string }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const pluginRef = useRef<PluginUIContext | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activePreset, setActivePreset] = useState<Preset>("rainbow");

  const handlePreset = useCallback(async (preset: Preset) => {
    if (!pluginRef.current) return;
    setActivePreset(preset);
    try {
      await applyPreset(pluginRef.current, preset);
    } catch (e) {
      console.error("Preset error:", e);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function init() {
      if (!containerRef.current) return;

      try {
        const res = await fetch(`${API_BASE}/adcs/${adcId}/structure`);
        if (!res.ok) {
          setError("Structure not available");
          setLoading(false);
          return;
        }
        const pdbData = await res.text();
        if (cancelled) return;

        const spec = DefaultPluginUISpec();
        const plugin = await createPluginUI({
          target: containerRef.current,
          spec: {
            ...spec,
            layout: {
              initial: {
                isExpanded: false,
                showControls: true,
                controlsDisplay: "landscape",
                regionState: {
                  left: "hidden",
                  top: "full",
                  right: "hidden",
                  bottom: "hidden",
                },
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

        // Apply rainbow (chain-id) coloring as default once hierarchy is ready
        const waitForStructure = () =>
          new Promise<void>((resolve) => {
            const check = () => {
              const s = plugin.managers.structure.hierarchy.current.structures;
              if (s.length > 0 && s[0].components && s[0].components.length > 0) {
                resolve();
              } else {
                setTimeout(check, 50);
              }
            };
            check();
          });
        await waitForStructure();
        await applyPreset(plugin, "rainbow", true);

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

  const presets: { key: Preset; label: string }[] = [
    { key: "rainbow", label: "Rainbow" },
    { key: "surface", label: "Surface" },
    { key: "interactions", label: "Interactions" },
  ];

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
        className="rounded-lg border border-border overflow-hidden relative molstar-container"
        style={{ height: 500 }}
      >
        {loading && (
          <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10">
            <p className="text-muted-foreground">Loading 3D viewer...</p>
          </div>
        )}
        {/* Preset buttons - top left corner over Mol* */}
        {!loading && !error && (
          <div className="absolute top-2 left-2 z-20 flex flex-col gap-1">
            {presets.map((p) => (
              <button
                key={p.key}
                onClick={() => handlePreset(p.key)}
                className={`px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
                  activePreset === p.key
                    ? "bg-primary text-primary-foreground"
                    : "bg-background/90 text-foreground hover:bg-muted border border-border"
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        )}
        <div ref={containerRef} style={{ width: "100%", height: "100%" }} />
      </div>
    </div>
  );
}
