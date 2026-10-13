import { NextRequest, NextResponse } from "next/server";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

export async function GET(request: NextRequest) {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: "Supabase non configuré" }, { status: 503 });
  }

  const q = request.nextUrl.searchParams.get("q")?.trim() ?? "";
  if (!q) {
    return NextResponse.json({ error: "Paramètre q requis" }, { status: 400 });
  }

  const supabase = getSupabaseAdmin();
  const pattern = `%${q}%`;

  const { data: brands, error: brandsError } = await supabase
    .from("brands")
    .select("id, name, country, logo_url")
    .ilike("name", pattern)
    .limit(5);

  if (brandsError) {
    return NextResponse.json({ error: brandsError.message }, { status: 500 });
  }

  const modelSelect =
    "id, name, generation, year_start, year_end, thumbnail_url, brands!inner(name)";

  const { data: modelsByName, error: modelsNameError } = await supabase
    .from("models")
    .select(modelSelect)
    .ilike("name", pattern)
    .limit(20);

  if (modelsNameError) {
    return NextResponse.json({ error: modelsNameError.message }, { status: 500 });
  }

  const brandIds = (brands ?? []).map((b) => b.id);
  let modelsByBrand: typeof modelsByName = [];

  if (brandIds.length > 0) {
    const { data, error } = await supabase
      .from("models")
      .select(modelSelect)
      .in("brand_id", brandIds)
      .limit(20);
    if (error) {
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    modelsByBrand = data ?? [];
  }

  const merged = new Map<number, (typeof modelsByName)[number]>();
  for (const m of [...(modelsByName ?? []), ...modelsByBrand]) {
    merged.set(m.id, m);
  }

  const models = [...merged.values()].slice(0, 20).map((m) => {
    const brand =
      m.brands && typeof m.brands === "object" && "name" in m.brands
        ? (m.brands as { name: string }).name
        : "";
    const { brands: _b, ...rest } = m;
    return { ...rest, brand_name: brand };
  });

  return NextResponse.json({
    query: q,
    brands: brands ?? [],
    models,
    total: (brands?.length ?? 0) + models.length,
  });
}
