// Deterministic, PURELY PRESENTATIONAL look titles (mirrors iOS LookTitles).
// The backend has no concept of outfit names; the design (artboards 05/07)
// shows editorial names like "The Long Walk", so we generate display names
// client-side, keyed by occasion + index. NEVER send these to the API.

const TITLES_BY_OCCASION: Record<string, string[]> = {
  casual: ['The Long Walk', 'Casual Friday', 'Corner Café', 'Open Air'],
  formal: ['Evening Edit', 'The Gallery', 'First Impression', 'Candlelight'],
  party: ['After Hours', 'The Guest List', 'Neon Nights', 'Last Dance'],
  business: ['The Boardroom', 'Nine to Five', 'Signature Move', 'Closing Note'],
  athletic: ['Morning Run', 'Second Wind', 'The Warm-Up', 'Fresh Pace'],
};

// Unknown occasions cycle the design artboard's sample names.
const FALLBACK = ['The Long Walk', 'Casual Friday', 'Evening Edit', 'Morning Run'];

/**
 * Title for the look at `index` (0-based) under `occasion`. Same inputs always
 * give the same title; consecutive indices cycle the list.
 */
export function lookTitle(occasion: string | null | undefined, index: number): string {
  const titles = TITLES_BY_OCCASION[(occasion ?? '').toLowerCase()] ?? FALLBACK;
  return titles[Math.max(index, 0) % titles.length];
}
