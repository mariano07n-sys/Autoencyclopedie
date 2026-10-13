import { NextResponse } from "next/server";
import { getSupabaseAdmin, isSupabaseConfigured } from "@/lib/supabase/admin";

export async function GET() {
  if (!isSupabaseConfigured()) {
    return NextResponse.json(
      { error: "Supabase non configuré sur ce déploiement" },
      { status: 503 }
    );
  }

  const supabase = getSupabaseAdmin();

  const [brands, models, specs, tasksDone, tasksPending] = await Promise.all([
    supabase.from("brands").select("*", { count: "exact", head: true }),
    supabase.from("models").select("*", { count: "exact", head: true }),
    supabase.from("specs").select("*", { count: "exact", head: true }),
    supabase
      .from("agent_tasks")
      .select("*", { count: "exact", head: true })
      .eq("status", "done"),
    supabase
      .from("agent_tasks")
      .select("*", { count: "exact", head: true })
      .eq("status", "pending"),
  ]);

  return NextResponse.json({
    brands: brands.count ?? 0,
    models: models.count ?? 0,
    specs: specs.count ?? 0,
    tasks_done: tasksDone.count ?? 0,
    tasks_pending: tasksPending.count ?? 0,
  });
}
