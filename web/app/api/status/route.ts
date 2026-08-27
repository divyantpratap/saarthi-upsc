import { hasSemanticIndex, loadIndex } from "@/lib/index-store";
import { MODEL } from "@/lib/gemini";

export const runtime = "nodejs";

/** Index health for the sidebar. Honest about what is and isn't loaded. */
export async function GET() {
  try {
    const { meta } = await loadIndex();
    const sources = Object.values(meta.sources);
    return Response.json({
      ok: true,
      chunks: meta.count,
      openChunks: meta.openCount,
      restrictedChunks: meta.restrictedCount,
      sources: sources.length,
      openSources: sources.filter((s) => s.tier === "A").length,
      builtAt: meta.builtAt,
      embedModel: meta.embedModel,
      retrievalMode: hasSemanticIndex(meta) ? "hybrid" : "lexical",
      configuredModel: MODEL,
    });
  } catch (error) {
    return Response.json(
      { ok: false, error: String(error), configuredModel: MODEL },
      { status: 503 },
    );
  }
}
