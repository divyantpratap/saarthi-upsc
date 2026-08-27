import { loadIndex } from "@/lib/index-store";

export const runtime = "nodejs";

/** The source manifest behind the library screen. */
export async function GET() {
  try {
    const { meta } = await loadIndex();
    const sources = Object.entries(meta.sources)
      .map(([key, record]) => ({ key, ...record }))
      .sort(
        (a, b) =>
          a.subject.localeCompare(b.subject) || a.file.localeCompare(b.file),
      );
    return Response.json({ ok: true, sources, builtAt: meta.builtAt });
  } catch (error) {
    return Response.json({ ok: false, error: String(error) }, { status: 503 });
  }
}
