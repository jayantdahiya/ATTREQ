// Pure helpers for the Profile hub identity + preferences rows (A5). No
// React/theme so they unit-test cleanly (mirrors the iOS ProfileScreen
// `initials`/`displayName` and `StylePreferencesValue`).

/**
 * Initials from the first two words of `fullName`; falls back to the email's
 * first letter, then "A". Uppercased. Mirrors iOS ProfileScreen.initials.
 */
export function profileInitials(
  fullName: string | null | undefined,
  email: string | null | undefined,
): string {
  const letters = (fullName ?? '')
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w.charAt(0))
    .join('')
    .toUpperCase();
  if (letters.length > 0) return letters;
  const first = (email ?? '').trim().charAt(0);
  return first ? first.toUpperCase() : 'A';
}

/** Full name, falling back to the email's local part, then "ATTREQ user". */
export function profileDisplayName(
  fullName: string | null | undefined,
  email: string | null | undefined,
): string {
  const trimmed = (fullName ?? '').trim();
  if (trimmed.length > 0) return trimmed;
  const local = (email ?? '').split('@')[0];
  if (local && local.length > 0) return local;
  return 'ATTREQ user';
}

/**
 * Classifies the backend `style_preferences` column. It is DNA-owned: the Style
 * DNA service stores `json.dumps(style_dna)` there and GET /users/me returns it
 * verbatim, so a value starting with `{` must be treated as "not set" (never
 * displayed, never round-tripped). Mirrors iOS StylePreferencesValue.parse.
 */
export type StylePreferencesValue =
  | { kind: 'dnaOwned' }
  | { kind: 'plain'; value: string }
  | { kind: 'empty' };

export function parseStylePreferences(raw: string | null | undefined): StylePreferencesValue {
  const trimmed = (raw ?? '').trim();
  if (trimmed.length === 0) return { kind: 'empty' };
  if (trimmed.startsWith('{')) return { kind: 'dnaOwned' };
  return { kind: 'plain', value: trimmed };
}

/** Row subtitle: plain chip string is shown; DNA JSON and blank read "Not set". */
export function stylePreferencesDisplay(raw: string | null | undefined): string {
  const parsed = parseStylePreferences(raw);
  return parsed.kind === 'plain' ? parsed.value : 'Not set';
}

/** ", "-separated parts for the editor prefill; empty unless the value is plain. */
export function stylePreferencesPrefillParts(raw: string | null | undefined): string[] {
  const parsed = parseStylePreferences(raw);
  if (parsed.kind !== 'plain') return [];
  return parsed.value
    .split(', ')
    .map((p) => p.trim())
    .filter(Boolean);
}
