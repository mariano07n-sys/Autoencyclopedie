import { NextRequest, NextResponse } from "next/server";
import { normalizeModelRow } from "@/lib/db/serialize";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

type RouteContext = { params: Promise<{ id: string }> };

export async function GET(_request: NextRequest, context: RouteContext) {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: "Supabase non configuré" }, { status: 503 });
  }

  const { id } = await context.params;
  const modelId = Number(id);
  if (Number.isNaN(modelId)) {
    return NextResponse.json({ error: "ID invalide" }, { status: 400 });
  }

  const supabase = getSupabaseAdmin();

  const { data: row, error } = await supabase
    .from("models")
    .select("*, brands!inner(name)")
    .eq("id", modelId)
    .maybeSingle();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  if (!row) {
    return NextResponse.json({ error: "Modèle non trouvé" }, { status: 404 });
  }

  const { data: specs, error: specsError } = await supabase
    .from("specs")
    .select("*")
    .eq("model_id", modelId);

  if (specsError) {
    return NextResponse.json({ error: specsError.message }, { status: 500 });
  }

  return NextResponse.json({
    ...normalizeModelRow(row),
    specs: specs ?? [],
  });
}
