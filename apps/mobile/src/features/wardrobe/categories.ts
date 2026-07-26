export type WardrobeFilter = 'all' | 'tops' | 'bottoms' | 'outer' | 'accents' | 'shoes';

export const WARDROBE_FILTERS: { key: WardrobeFilter; label: string }[] = [
  { key: 'all', label: 'All' },
  { key: 'tops', label: 'Tops' },
  { key: 'bottoms', label: 'Bottoms' },
  { key: 'outer', label: 'Outer' },
  { key: 'accents', label: 'Accents' },
  { key: 'shoes', label: 'Shoes' },
];

// Free-text backend category → chip bucket. Precedence bottoms → shoes → outer →
// accents → tops (mirrors iOS WardrobeFilter.bucket / RN toneForCategory).
export function bucketFor(category: string | null | undefined): WardrobeFilter {
  const v = (category ?? '').toLowerCase();
  if (/bottom|pant|trouser|jean|skirt|short|chino|legging/.test(v)) return 'bottoms';
  if (/shoe|sneaker|sandal|boot|heel/.test(v)) return 'shoes';
  if (/outer|coat|jacket|blazer/.test(v)) return 'outer';
  if (/bag|belt|hat|scarf|jewel|accessor/.test(v)) return 'accents';
  return 'tops';
}

export function matchesFilter(filter: WardrobeFilter, category: string | null | undefined): boolean {
  return filter === 'all' || bucketFor(category) === filter;
}
