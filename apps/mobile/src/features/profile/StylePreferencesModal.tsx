import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { Chip } from '@/design-system/components/Chip';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import { ProfileSheet } from '@/features/profile/ProfileSheet';
import { parseStylePreferences, stylePreferencesPrefillParts } from '@/features/profile/profileFormat';
import { useUpdateProfile } from '@/lib/query/users';

// Kept in sync with the register wizard's style options (artboard 03).
const STYLE_OPTIONS = ['Minimal', 'Earthy', 'Tailored', 'Layered', 'Casual', 'Formal', 'Streetwear', 'Athleisure'];

/**
 * Style-preferences editor (Profile preferences). Keyword chips + occasions
 * input. BACKEND DIVERGENCE (documented, mirrors iOS StylePreferencesSheet):
 * the backend `users.style_preferences` column is DNA-OWNED and `PUT /users/me`
 * (UserUpdate) does NOT accept a `style_preferences` field, so the value is
 * effectively DEVICE-LOCAL — the PUT is best-effort and its result never blocks
 * the sheet. When the loaded value is the Style DNA JSON blob, the PUT is
 * skipped entirely and a "Saved on this device only" echo is shown so we never
 * risk overwriting the DNA blob.
 */
export function StylePreferencesModal({
  visible,
  onClose,
  current,
}: {
  visible: boolean;
  onClose: () => void;
  current: string | null | undefined;
}) {
  const t = useTheme();
  const update = useUpdateProfile();
  const [selected, setSelected] = useState<string[]>([]);
  const [occasions, setOccasions] = useState('');
  const [localOnlyHint, setLocalOnlyHint] = useState<string | null>(null);

  const isDnaOwned = parseStylePreferences(current).kind === 'dnaOwned';

  useEffect(() => {
    if (!visible) return;
    const parts = stylePreferencesPrefillParts(current);
    setSelected(parts.filter((p) => STYLE_OPTIONS.includes(p)));
    setOccasions(parts.filter((p) => !STYLE_OPTIONS.includes(p)).join(', '));
    setLocalOnlyHint(null);
  }, [visible, current]);

  const toggle = (kw: string) =>
    setSelected((cur) => (cur.includes(kw) ? cur.filter((k) => k !== kw) : [...cur, kw]));

  const save = () => {
    if (isDnaOwned) {
      // Never PUT over the DNA blob — echo a device-local confirmation instead.
      setLocalOnlyHint('Saved on this device only.');
      setTimeout(onClose, 900);
      return;
    }
    const parts = [...selected];
    const trimmed = occasions.trim();
    if (trimmed.length > 0) parts.push(trimmed);
    update.mutate(
      { style_preferences: parts.length > 0 ? parts.join(', ') : undefined },
      {
        // Best-effort: success or failure, the sheet dismisses (see header).
        onSettled: onClose,
      },
    );
  };

  return (
    <ProfileSheet visible={visible} onClose={onClose} headerLabel="Preferences — Style" testID="style-sheet">
      <Text style={[display(26), { color: t.colors.text, marginBottom: 6 }]}>Refine your aesthetic.</Text>
      <BodyText size={13} style={{ marginBottom: 20 }}>
        Keywords steer what we suggest each morning.
      </BodyText>

      <Card padding={20}>
        <MonoLabel style={{ marginBottom: 14 }}>Style keywords</MonoLabel>
        <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 7, marginBottom: 20 }}>
          {STYLE_OPTIONS.map((kw) => (
            <Chip key={kw} label={kw} selected={selected.includes(kw)} onPress={() => toggle(kw)} />
          ))}
        </View>
        <View style={{ height: 1, backgroundColor: t.colors.borderSoft, marginBottom: 18 }} />
        <UnderlineInput
          label="Occasions (optional)"
          value={occasions}
          onChangeText={setOccasions}
          autoCapitalize="none"
          testID="style-occasions"
        />
      </Card>

      <PrimaryButton
        label="Save preferences"
        variant="accent"
        isLoading={update.isPending}
        onPress={save}
        testID="style-save"
      />
      {localOnlyHint && (
        <BodyText size={12} style={{ marginTop: 10, textAlign: 'center' }}>
          {localOnlyHint}
        </BodyText>
      )}
      <View style={{ height: 8 }} />
    </ProfileSheet>
  );
}
