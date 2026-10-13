type JsonField = string[] | unknown;

function parseJsonArray(value: unknown): string[] {
  if (Array.isArray(value)) return value as string[];
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

export type NormalizedModel = Record<string, unknown> & {
  brand_name?: string;
  body_styles: string[];
  image_urls: string[];
  countries: string[];
};

export function normalizeModelRow(
  row: Record<string, unknown> & { brands?: { name: string } | null }
): NormalizedModel {
  const brandName =
    (row.brand_name as string | undefined) ??
    (row.brands && typeof row.brands === "object" && "name" in row.brands
      ? (row.brands as { name: string }).name
      : undefined);

  const { brands: _b, ...rest } = row;
  return {
    ...rest,
    brand_name: brandName,
    body_styles: parseJsonArray(row.body_styles as JsonField),
    image_urls: parseJsonArray(row.image_urls as JsonField),
    countries: parseJsonArray(row.countries as JsonField),
  };
}
