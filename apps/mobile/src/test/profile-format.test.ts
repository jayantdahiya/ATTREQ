import {
  parseStylePreferences,
  profileDisplayName,
  profileInitials,
  stylePreferencesDisplay,
  stylePreferencesPrefillParts,
} from '@/features/profile/profileFormat';

describe('profileInitials', () => {
  it('uses the first two words of the full name', () => {
    expect(profileInitials('Natasha Volkov', 'x@y.com')).toBe('NV');
    expect(profileInitials('  ada   lovelace  babbage', 'x@y.com')).toBe('AL');
  });
  it('handles a single-word name', () => {
    expect(profileInitials('Cher', 'x@y.com')).toBe('C');
  });
  it('falls back to the email first letter, then "A"', () => {
    expect(profileInitials('', 'zoe@example.com')).toBe('Z');
    expect(profileInitials(null, null)).toBe('A');
    expect(profileInitials('   ', '')).toBe('A');
  });
});

describe('profileDisplayName', () => {
  it('prefers the trimmed full name', () => {
    expect(profileDisplayName('  Grace Hopper ', 'g@navy.mil')).toBe('Grace Hopper');
  });
  it('falls back to the email local part', () => {
    expect(profileDisplayName('', 'grace@navy.mil')).toBe('grace');
    expect(profileDisplayName(null, 'grace@navy.mil')).toBe('grace');
  });
  it('falls back to "ATTREQ user" when nothing is available', () => {
    expect(profileDisplayName(null, null)).toBe('ATTREQ user');
    expect(profileDisplayName('', '')).toBe('ATTREQ user');
  });
});

describe('parseStylePreferences', () => {
  it('classifies a DNA JSON blob as dnaOwned (never displayed)', () => {
    expect(parseStylePreferences('{"aesthetic":{}}').kind).toBe('dnaOwned');
    expect(parseStylePreferences('   { "x": 1 }').kind).toBe('dnaOwned');
  });
  it('classifies a plain chip string', () => {
    expect(parseStylePreferences('Minimal, Earthy')).toEqual({ kind: 'plain', value: 'Minimal, Earthy' });
  });
  it('classifies blank / null as empty', () => {
    expect(parseStylePreferences(null).kind).toBe('empty');
    expect(parseStylePreferences('   ').kind).toBe('empty');
  });
});

describe('stylePreferencesDisplay', () => {
  it('shows a plain value, "Not set" for DNA-owned or empty', () => {
    expect(stylePreferencesDisplay('Minimal, Earthy')).toBe('Minimal, Earthy');
    expect(stylePreferencesDisplay('{"a":1}')).toBe('Not set');
    expect(stylePreferencesDisplay(null)).toBe('Not set');
  });
});

describe('stylePreferencesPrefillParts', () => {
  it('splits a plain value on ", "', () => {
    expect(stylePreferencesPrefillParts('Minimal, Earthy, weekend dinners')).toEqual([
      'Minimal',
      'Earthy',
      'weekend dinners',
    ]);
  });
  it('is empty for DNA-owned or blank values', () => {
    expect(stylePreferencesPrefillParts('{"a":1}')).toEqual([]);
    expect(stylePreferencesPrefillParts(null)).toEqual([]);
  });
});
