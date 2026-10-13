import { NextRequest, NextResponse } from "next/server";
import { normalizeModelRow } from "@/lib/db/serialize";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

export async function GET(request: NextRequest) {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: "Supabase non configuré" }, { status: 503 });
  }

  const { searchParams } = request.nextUrl;
  const brandId = searchParams.get("brand_id");
  const yearFrom = searchParams.get("year_from");
  const yearTo = searchParams.get("year_to");
  const segment = searchParams.get("segment");
  const search = searchParams.get("search");

  const supabase = getSupabaseAdmin();
  let query = supabase
    .from("models")
    .select("*, brands!inner(name)")
    .order("year_start")
    .limit(1000);

  if (brandId) query = query.eq("brand_id", Number(brandId));
  if (yearFrom) query = query.gte("year_start", Number(yearFrom));
  if (yearTo) {
    query = query.or(`year_end.lte.${Number(yearTo)},year_end.is.null`);
  }
  if (segment) query = query.eq("segment", segment);

  const { data, error } = await query;
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  let models = (data ?? []).map((row) => normalizeModelRow(row));

  if (search) {
    const q = search.toLowerCase();
    models = models.filter((m) => {
      const name = String(m.name ?? "");
      const brand = String(m.brand_name ?? "");
      return name.toLowerCase().includes(q) || brand.toLowerCase().includes(q);
    });
  }

  return NextResponse.json({ models, total: models.length });
}
