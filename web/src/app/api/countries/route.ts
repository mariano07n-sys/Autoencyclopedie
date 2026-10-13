import { NextResponse } from "next/server";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

export async function GET() {
  if (!isSupabaseConfigured()) {
    return NextResponse.json({ error: "Supabase non configuré" }, { status: 503 });
  }

  const supabase = getSupabaseAdmin();
  const { data, error } = await supabase
    .from("brands")
    .select("country")
    .not("country", "is", null)
    .order("country");

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }

  const countries = [...new Set((data ?? []).map((r) => r.country as string))].sort();

  return NextResponse.json({ countries });
}
