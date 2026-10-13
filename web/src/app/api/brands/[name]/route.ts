import { NextRequest, NextResponse } from "next/server";
import { normalizeModelRow } from "@/lib/db/serialize";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

type RouteContext = { params: Promise<{ name: string }> };

export async function GET(_request: NextRequest, context: RouteContext) {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: "Supabase non configuré" }, { status: 503 });
  }

  const { name: rawName } = await context.params;
  const name = decodeURIComponent(rawName);
  const supabase = getSupabaseAdmin();

  const { data: brand, error } = await supabase
    .from("brands")
    .select("*")
    .ilike("name", name)
    .maybeSingle();

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
  if (!brand) {
    return NextResponse.json({ error: "Marque non trouvée" }, { status: 404 });
  }

  const { data: models, error: modelsError } = await supabase
    .from("models")
    .select("*")
    .eq("brand_id", brand.id)
    .order("year_start");

  if (modelsError) {
    return NextResponse.json({ error: modelsError.message }, { status: 500 });
  }

  return NextResponse.json({
    ...brand,
    models: (models ?? []).map((m) => normalizeModelRow(m)),
  });
}
