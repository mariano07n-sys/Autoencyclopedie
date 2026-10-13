import { NextResponse } from "next/server";
import type { NormalizedModel } from "@/lib/db/serialize";
import { normalizeModelRow } from "@/lib/db/serialize";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

export async function GET() {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: "Supabase non configuré" }, { status: 503 });
  }

  const supabase = getSupabaseAdmin();
  const { data, error } = await supabase
    .from("models")
    .select("*, brands!inner(name)")
    .not("year_start", "is", null)
    .order("year_start", { ascending: true })
    .limit(1000);

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const models = (data ?? []).map((row) => normalizeModelRow(row));

  const byDecade = new Map<number, NormalizedModel[]>();
  for (const model of models) {
    const year = Number(model.year_start);
    if (!Number.isFinite(year)) continue;
    const decade = Math.floor(year / 10) * 10;
    const bucket = byDecade.get(decade);
    if (bucket) bucket.push(model);
    else byDecade.set(decade, [model]);
  }

  const decades = [...byDecade.entries()]
    .sort((a, b) => a[0] - b[0])
    .map(([decade, bucket]) => ({ decade, models: bucket }));

  return NextResponse.json({ decades, total: models.length });
}
