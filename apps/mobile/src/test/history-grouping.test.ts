import { dayKeyFor, groupOutfits, piecesCount, pillFor } from '@/features/history/historyGrouping';
import type { Outfit } from '@/lib/api/types';

function makeOutfit(overrides: Partial<Outfit> = {}): Outfit {
  return {
    id: 'o1',
    user_id: 'u1',
    top_item_id: 'top-1',
    bottom_item_id: 'bottom-1',
    accessory_ids: null,
    occasion_context: 'casual',
    footwear_item_id: null,
    outerwear_item_id: null,
    fullbody_item_id: null,
    worn_date: null,
    feedback_score: null,
    weather_context: null,
    created_at: '2026-06-23T09:00:00Z',
    updated_at: '2026-06-23T09:00:00Z',
    ...overrides,
  };
}

describe('historyGrouping', () => {
  describe('pillFor precedence (feedback beats worn)', () => {
    it('feedback_score 1 -> loved, even with a worn_date', () => {
      expect(pillFor(makeOutfit({ feedback_score: 1, worn_date: '2026-06-23' }))).toBe('loved');
    });
    it('feedback_score -1 -> skipped, even with a worn_date', () => {
      expect(pillFor(makeOutfit({ feedback_score: -1, worn_date: '2026-06-23' }))).toBe('skipped');
    });
    it('worn_date set (no/neutral feedback) -> worn', () => {
      expect(pillFor(makeOutfit({ worn_date: '2026-06-23' }))).toBe('worn');
      expect(pillFor(makeOutfit({ feedback_score: 0, worn_date: '2026-06-23' }))).toBe('worn');
    });
    it('nothing set -> tracked', () => {
      expect(pillFor(makeOutfit())).toBe('tracked');
    });
  });

  describe('dayKeyFor uses worn_date verbatim, else the LOCAL day of created_at', () => {
    it('prefers worn_date exactly as stored', () => {
      expect(dayKeyFor(makeOutfit({ worn_date: '2026-06-20' }))).toBe('2026-06-20');
    });
    it('falls back to the local calendar day of created_at', () => {
      // Local-time constructor so the assertion is timezone-independent.
      const created = new Date(2026, 5, 23, 22, 0).toISOString();
      expect(dayKeyFor(makeOutfit({ worn_date: null, created_at: created }))).toBe('2026-06-23');
    });
  });

  it('piecesCount counts non-null top/bottom/fullbody + accessories', () => {
    expect(piecesCount(makeOutfit())).toBe(2);
    expect(piecesCount(makeOutfit({ accessory_ids: ['a1', 'a2'] }))).toBe(4);
    expect(piecesCount(makeOutfit({ top_item_id: null, bottom_item_id: null, fullbody_item_id: 'fb' }))).toBe(1);
  });

  it('groupOutfits groups by day, newest day first, server order within a group', () => {
    const outfits = [
      makeOutfit({ id: 'a', worn_date: '2026-06-23' }),
      makeOutfit({ id: 'b', worn_date: '2026-06-25' }),
      makeOutfit({ id: 'c', worn_date: '2026-06-23' }),
    ];
    const groups = groupOutfits(outfits);
    expect(groups.map((g) => g.isoLabel)).toEqual(['2026-06-25', '2026-06-23']);
    expect(groups[1].entries.map((e) => e.outfit.id)).toEqual(['a', 'c']);
    // Titles are keyed by position within the group.
    expect(groups[1].entries[0].title).toBe('The Long Walk');
    expect(groups[1].entries[1].title).toBe('Casual Friday');
  });
});
