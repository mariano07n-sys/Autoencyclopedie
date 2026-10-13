import { NextRequest, NextResponse } from "next/server";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

export async function GET(request: NextRequest) {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: "Supabase non configuré" }, { status: 503 });
  }

  const { searchParams } = request.nextUrl;
  const search = searchParams.get("search");
  const country = searchParams.get("country");

  const supabase = getSupabaseAdmin();
  let query = supabase.from("brands").select("*").order("name");

  if (country) {
    query = query.eq("country", country);
  }
  if (search) {
    query = query.ilike("name", `%${search}%`);
  }

  const { data, error } = await query;
  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  let brands = data ?? [];
  if (search && country) {
    const s = search.toLowerCase();
    brands = brands.filter(
      (b) =>
        b.name.toLowerCase().includes(s) ||
        (b.country && b.country.toLowerCase().includes(s))
    );
  }

  return NextResponse.json({ brands, total: brands.length });
}
