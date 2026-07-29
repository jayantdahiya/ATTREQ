import { lookTitle } from '@/features/today/lookTitles';

describe('lookTitle', () => {
  it('is deterministic and cycles the per-occasion list by index', () => {
    expect(lookTitle('casual', 0)).toBe('The Long Walk');
    expect(lookTitle('casual', 1)).toBe('Casual Friday');
    expect(lookTitle('casual', 4)).toBe('The Long Walk'); // wraps (4 % 4)
    expect(lookTitle('formal', 0)).toBe('Evening Edit');
    expect(lookTitle('business', 2)).toBe('Signature Move');
  });

  it('is case-insensitive on the occasion key', () => {
    expect(lookTitle('CASUAL', 0)).toBe(lookTitle('casual', 0));
  });

  it('falls back for unknown / null occasions', () => {
    expect(lookTitle('brunch', 0)).toBe('The Long Walk');
    expect(lookTitle(null, 2)).toBe('Evening Edit');
    expect(lookTitle(undefined, 3)).toBe('Morning Run');
  });

  it('clamps negative indices to 0', () => {
    expect(lookTitle('casual', -3)).toBe('The Long Walk');
  });
});
