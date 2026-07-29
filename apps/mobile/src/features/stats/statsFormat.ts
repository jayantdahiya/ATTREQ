// Pure presentation helpers for the wardrobe stats surfaces (A5). Kept free of
// React/theme so they can be unit-tested in isolation (mirrors the iOS
// StatsScreen private formatters). Numbers come straight off /stats/wardrobe
// and /stats/forgotten (schemas/stats.py).

import type {
  CostPerWearEntry,
  ForgottenItemEntry,
  WardrobeStatsResponse,
  WornItemEntry,
} from '@/lib/api/types';

/** "$1234.50" — two decimals, matching the iOS `currency` formatter. */
export function formatCurrency(value: number): string {
  return '$' + value.toFixed(2);
}

/** Whole-percent string from a 0–100 fraction, e.g. 24.6 → "25%". */
export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}

/** Title-case a single word, leaving the rest of the string untouched. */
function capitalize(word: string): string {
  if (!word) return word;
  return word.charAt(0).toUpperCase() + word.slice(1);
}

/** "Blue Shirt" from category + primary color; "Piece" when category is null. */
export function itemTitle(category: string | null, color: string | null): string {
  const name = category ? capitalize(category) : 'Piece';
  if (!color || color.length === 0) return name;
  return `${capitalize(color)} ${name}`;
}

/**
 * Mean cost-per-wear across the entries that have actually been worn (a null
 * `cost_per_wear` means "priced but never worn" and is excluded). Returns null
 * when no entry qualifies — the caller shows "—" rather than "$0.00".
 */
export function averageCostPerWear(entries: CostPerWearEntry[]): number | null {
  const worn = entries.filter((e) => e.cost_per_wear != null);
  if (worn.length === 0) return null;
  const total = worn.reduce((sum, e) => sum + (e.cost_per_wear ?? 0), 0);
  return total / worn.length;
}

export interface StatTile {
  label: string;
  value: string;
  /** Rendered in the clay accent color (a nudge, not neutral). */
  accent?: boolean;
}

/**
 * The three Profile identity-card tiles, all sourced from /stats/wardrobe per
 * the A5 spec: pieces, cost-per-wear, worn. `null` stats (still loading /
 * errored) yields placeholder dashes so the row keeps its shape.
 */
export function profileStatTiles(stats: WardrobeStatsResponse | null | undefined): StatTile[] {
  const avg = stats ? averageCostPerWear(stats.cost_per_wear) : null;
  return [
    { label: 'Pieces', value: stats ? String(stats.total_active_items) : '—' },
    {
      label: 'Cost / wear',
      value: avg != null ? formatCurrency(avg) : '—',
      accent: true,
    },
    { label: 'Worn 30d', value: stats ? String(stats.worn_last_30_days) : '—' },
  ];
}

/** Most/least-worn row subtitle. */
export function wornSubtitle(entry: WornItemEntry): string {
  return entry.last_worn ? `Last worn ${entry.last_worn}` : 'Not worn yet';
}

/** "N outfit(s)" pill copy for a worn entry. */
export function outfitCountLabel(count: number): string {
  return `${count} outfit${count === 1 ? '' : 's'}`;
}

/** Forgotten-item row subtitle — never worn / not worn in N days / worn N outfits. */
export function forgottenSubtitle(entry: ForgottenItemEntry): string {
  if (entry.wear_count === 0) return 'Never worn';
  if (entry.days_since_worn != null) {
    const d = entry.days_since_worn;
    return `Not worn in ${d} day${d === 1 ? '' : 's'}`;
  }
  return `Worn in ${outfitCountLabel(entry.wear_count)}`;
}

/** True when the whole dashboard is effectively empty (a fresh account). */
export function isWardrobeStatsEmpty(stats: WardrobeStatsResponse): boolean {
  return stats.total_active_items === 0;
}
