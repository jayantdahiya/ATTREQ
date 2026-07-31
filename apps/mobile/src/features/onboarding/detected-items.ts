import type { DetectedWardrobeItem, StyleDnaUploadResponse } from '@/lib/api/types';

// Flattens the detected wardrobe items out of every photo's
// `per_photo_extraction.wardrobe_items_detected` blob — the same collection the
// iOS OnboardingViewModel.extractDetectedItems builds. The extraction JSON is
// produced by a Python backend (snake_case), but keys are looked up in BOTH
// camelCase and snake_case so a runtime that rewrites keys is tolerated too.

type Dict = Record<string, unknown>;

function toSnake(camelKey: string): string {
  return camelKey.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
}

/** Looks up `camelKey`, falling back to its snake_case spelling. */
function field(obj: Dict, camelKey: string): unknown {
  if (camelKey in obj) return obj[camelKey];
  return obj[toSnake(camelKey)];
}

function asString(value: unknown): string | null {
  if (typeof value !== 'string') return null;
  const trimmed = value.trim();
  return trimmed.length > 0 ? trimmed : null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.filter((v): v is string => typeof v === 'string');
}

function asNumber(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : 0;
}

function detectedItem(value: unknown): DetectedWardrobeItem | null {
  if (typeof value !== 'object' || value === null) return null;
  const fields = value as Dict;
  const category = asString(field(fields, 'category'));
  if (!category) return null;
  return {
    category,
    subcategory: asString(field(fields, 'subcategory')) ?? '',
    colorPrimary: asString(field(fields, 'colorPrimary')),
    colorSecondary: asString(field(fields, 'colorSecondary')),
    pattern: asString(field(fields, 'pattern')),
    occasion: asStringArray(field(fields, 'occasion')),
    season: asStringArray(field(fields, 'season')),
    confidence: asNumber(field(fields, 'confidence')),
    boundingRegion: asString(field(fields, 'boundingRegion')) ?? '',
  };
}

export function extractDetectedItems(response: StyleDnaUploadResponse): DetectedWardrobeItem[] {
  const out: DetectedWardrobeItem[] = [];
  for (const photo of response.photos ?? []) {
    const extraction = photo.per_photo_extraction;
    if (!extraction) continue;
    const detected = field(extraction as Dict, 'wardrobeItemsDetected');
    if (!Array.isArray(detected)) continue;
    for (const value of detected) {
      const item = detectedItem(value);
      if (item) out.push(item);
    }
  }
  return out;
}

/** Display title for a detected item (subcategory preferred, capitalized). */
export function detectedItemTitle(item: DetectedWardrobeItem): string {
  const name = item.subcategory.length > 0 ? item.subcategory : item.category;
  return name.charAt(0).toUpperCase() + name.slice(1);
}

/** Secondary "color · pattern" detail line for a detected item. */
export function detectedItemDetail(item: DetectedWardrobeItem): string {
  const parts: string[] = [];
  if (item.colorPrimary) {
    parts.push(item.colorSecondary ? `${item.colorPrimary} / ${item.colorSecondary}` : item.colorPrimary);
  }
  if (item.pattern) parts.push(item.pattern);
  return parts.length > 0 ? parts.join(' · ') : item.category;
}

/**
 * "N wardrobe items found" preview line: first three "color name" pairs joined
 * with " · ", then "+N more" (mirrors iOS ResultsView.itemsPreview / RN
 * FoundItemsCard).
 */
export function detectedItemsPreview(items: DetectedWardrobeItem[]): string {
  const names = items.slice(0, 3).map((item) => {
    const name = item.subcategory.length > 0 ? item.subcategory : item.category;
    return [item.colorPrimary, name].filter(Boolean).join(' ');
  });
  const remaining = items.length - 3;
  return names.join(' · ') + (remaining > 0 ? ` · +${remaining} more` : '');
}
