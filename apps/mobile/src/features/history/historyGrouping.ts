import type { PillVariant } from '@/design-system/components/Pill';
import { historyDateLabel, localDayOf } from '@/lib/utils/dates';
import { lookTitle } from '@/features/today/lookTitles';
import type { Outfit } from '@/lib/api/types';

// History grouping/pill logic (mirrors iOS HistoryViewModel). Kept pure so the
// precedence + local-day rules are unit-testable.

export type HistoryPill = 'loved' | 'skipped' | 'worn' | 'tracked';

export const PILL_LABEL: Record<HistoryPill, string> = {
  loved: 'Loved',
  skipped: 'Skipped',
  worn: 'Worn',
  tracked: 'Tracked',
};

export const PILL_VARIANT: Record<HistoryPill, PillVariant> = {
  loved: 'gold',
  skipped: 'clay',
  worn: 'moss',
  tracked: 'muted',
};

/**
 * Pill precedence: feedback BEATS worn. feedback_score 1 -> Loved (gold),
 * -1 -> Skipped (clay), else worn_date set -> Worn (moss), else Tracked
 * (muted). A feedback_score of 0/null falls through to the worn check.
 */
export function pillFor(outfit: Outfit): HistoryPill {
  if (outfit.feedback_score === 1) return 'loved';
  if (outfit.feedback_score === -1) return 'skipped';
  if (outfit.worn_date) return 'worn';
  return 'tracked';
}

/** Non-null item ids: top + bottom + fullbody + each accessory. */
export function piecesCount(outfit: Outfit): number {
  return (
    (outfit.top_item_id ? 1 : 0) +
    (outfit.bottom_item_id ? 1 : 0) +
    (outfit.fullbody_item_id ? 1 : 0) +
    (outfit.accessory_ids?.length ?? 0)
  );
}

/** Group key: worn_date verbatim, else the LOCAL calendar day of created_at. */
export function dayKeyFor(outfit: Outfit): string {
  if (outfit.worn_date) return outfit.worn_date;
  return localDayOf(outfit.created_at);
}

export interface HistoryEntry {
  outfit: Outfit;
  title: string;
  pieces: number;
  pill: HistoryPill;
}

export interface HistoryGroup {
  isoLabel: string;
  dateLabel: string;
  entries: HistoryEntry[];
}

/**
 * Group a flat, server-ordered outfit list into day sections, newest day
 * first, entries in server order within a group. Titles are the editorial
 * `lookTitle`s keyed by occasion + position within the group.
 */
export function groupOutfits(outfits: Outfit[]): HistoryGroup[] {
  const keyed = new Map<string, Outfit[]>();
  for (const outfit of outfits) {
    const key = dayKeyFor(outfit);
    const bucket = keyed.get(key);
    if (bucket) bucket.push(outfit);
    else keyed.set(key, [outfit]);
  }
  return [...keyed.keys()]
    .sort((a, b) => (a < b ? 1 : a > b ? -1 : 0))
    .map((key) => ({
      isoLabel: key,
      dateLabel: historyDateLabel(key),
      entries: (keyed.get(key) ?? []).map((outfit, index) => ({
        outfit,
        title: lookTitle(outfit.occasion_context, index),
        pieces: piecesCount(outfit),
        pill: pillFor(outfit),
      })),
    }));
}
