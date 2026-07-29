import {
  averageCostPerWear,
  forgottenSubtitle,
  formatCurrency,
  formatPercent,
  itemTitle,
  outfitCountLabel,
  profileStatTiles,
  wornSubtitle,
} from '@/features/stats/statsFormat';
import type {
  CostPerWearEntry,
  ForgottenItemEntry,
  WardrobeStatsResponse,
  WornItemEntry,
} from '@/lib/api/types';

const cpw = (over: Partial<CostPerWearEntry>): CostPerWearEntry => ({
  item_id: 'i',
  category: 'shirt',
  color_primary: 'blue',
  thumbnail_url: null,
  purchase_price: 100,
  wear_count: 5,
  cost_per_wear: 20,
  ...over,
});

describe('formatCurrency / formatPercent', () => {
  it('formats currency to two decimals with a leading $', () => {
    expect(formatCurrency(0)).toBe('$0.00');
    expect(formatCurrency(1234.5)).toBe('$1234.50');
    expect(formatCurrency(19.999)).toBe('$20.00');
  });

  it('rounds percent to a whole number', () => {
    expect(formatPercent(24.6)).toBe('25%');
    expect(formatPercent(0)).toBe('0%');
    expect(formatPercent(33.2)).toBe('33%');
  });
});

describe('itemTitle', () => {
  it('capitalizes color + category', () => {
    expect(itemTitle('shirt', 'blue')).toBe('Blue Shirt');
  });
  it('drops the color when absent', () => {
    expect(itemTitle('shirt', null)).toBe('Shirt');
    expect(itemTitle('shirt', '')).toBe('Shirt');
  });
  it('falls back to "Piece" when the category is null', () => {
    expect(itemTitle(null, 'blue')).toBe('Blue Piece');
    expect(itemTitle(null, null)).toBe('Piece');
  });
});

describe('averageCostPerWear', () => {
  it('averages only entries with a non-null cost_per_wear', () => {
    const entries = [
      cpw({ cost_per_wear: 10 }),
      cpw({ cost_per_wear: 30 }),
      cpw({ cost_per_wear: null }), // priced but never worn — excluded
    ];
    expect(averageCostPerWear(entries)).toBe(20);
  });
  it('returns null when nothing qualifies', () => {
    expect(averageCostPerWear([])).toBeNull();
    expect(averageCostPerWear([cpw({ cost_per_wear: null })])).toBeNull();
  });
});

describe('profileStatTiles', () => {
  const stats = {
    total_active_items: 12,
    cost_per_wear: [cpw({ cost_per_wear: 10 }), cpw({ cost_per_wear: 20 })],
    worn_last_30_days: 4,
  } as unknown as WardrobeStatsResponse;

  it('derives pieces / cost-per-wear / worn from /stats/wardrobe', () => {
    const tiles = profileStatTiles(stats);
    expect(tiles.map((t) => t.label)).toEqual(['Pieces', 'Cost / wear', 'Worn 30d']);
    expect(tiles[0].value).toBe('12');
    expect(tiles[1].value).toBe('$15.00');
    expect(tiles[2].value).toBe('4');
  });

  it('shows placeholder dashes when stats are missing', () => {
    const tiles = profileStatTiles(null);
    expect(tiles.map((t) => t.value)).toEqual(['—', '—', '—']);
  });

  it('shows a dash for cost-per-wear when nothing has been worn', () => {
    const tiles = profileStatTiles({
      total_active_items: 3,
      cost_per_wear: [cpw({ cost_per_wear: null })],
      worn_last_30_days: 0,
    } as unknown as WardrobeStatsResponse);
    expect(tiles[1].value).toBe('—');
  });
});

describe('wornSubtitle / outfitCountLabel', () => {
  it('describes last-worn state', () => {
    expect(wornSubtitle({ last_worn: '2026-07-01' } as WornItemEntry)).toBe('Last worn 2026-07-01');
    expect(wornSubtitle({ last_worn: null } as WornItemEntry)).toBe('Not worn yet');
  });
  it('pluralizes outfit counts', () => {
    expect(outfitCountLabel(1)).toBe('1 outfit');
    expect(outfitCountLabel(3)).toBe('3 outfits');
  });
});

describe('forgottenSubtitle', () => {
  const base = (over: Partial<ForgottenItemEntry>): ForgottenItemEntry => ({
    item_id: 'i',
    category: 'coat',
    color_primary: null,
    thumbnail_url: null,
    wear_count: 0,
    last_worn: null,
    days_since_worn: null,
    best_partner: null,
    ...over,
  });

  it('says "Never worn" for zero-wear items', () => {
    expect(forgottenSubtitle(base({ wear_count: 0 }))).toBe('Never worn');
  });
  it('reports days since worn when available', () => {
    expect(forgottenSubtitle(base({ wear_count: 2, days_since_worn: 90 }))).toBe('Not worn in 90 days');
    expect(forgottenSubtitle(base({ wear_count: 2, days_since_worn: 1 }))).toBe('Not worn in 1 day');
  });
  it('falls back to outfit count when no days_since_worn', () => {
    expect(forgottenSubtitle(base({ wear_count: 3, days_since_worn: null }))).toBe('Worn in 3 outfits');
  });
});
