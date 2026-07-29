import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import { ProfileSheet } from '@/features/profile/ProfileSheet';
import { useUpdateProfile } from '@/lib/query/users';
import { describeAuthError } from '@/lib/api/errors';

/**
 * Location editor (Profile preferences). Manual city only — device-location
 * capture is DEFERRED on Android (same as the A1 register wizard's manual-city
 * path). Saves via PUT /users/me (location + saved_city); the PATCH
 * /users/me/location endpoint requires coordinates, so the city-only path uses
 * PUT — mirrors the iOS LocationEditSheet city-only branch. Any previously
 * saved coordinates are left untouched.
 */
export function LocationEditModal({
  visible,
  onClose,
  initialCity,
}: {
  visible: boolean;
  onClose: () => void;
  initialCity: string;
}) {
  const t = useTheme();
  const update = useUpdateProfile();
  const [city, setCity] = useState(initialCity);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (visible) {
      setCity(initialCity);
      setError(null);
    }
  }, [visible, initialCity]);

  const save = () => {
    const trimmed = city.trim();
    if (trimmed.length === 0) {
      setError('Enter your city.');
      return;
    }
    setError(null);
    update.mutate(
      { location: trimmed, saved_city: trimmed },
      {
        onSuccess: onClose,
        onError: (e) => setError(describeAuthError(e)),
      },
    );
  };

  return (
    <ProfileSheet visible={visible} onClose={onClose} headerLabel="Preferences — Location" testID="location-sheet">
      <Text style={[display(26), { color: t.colors.text, marginBottom: 6 }]}>Where mornings find you.</Text>
      <BodyText size={13} style={{ marginBottom: 20 }}>
        Your city keeps suggestions weather-aware.
      </BodyText>

      <Card padding={20}>
        <UnderlineInput
          label="Your city"
          value={city}
          onChangeText={setCity}
          autoCapitalize="words"
          placeholder="e.g. Milan"
          testID="location-city"
        />
      </Card>

      {error && (
        <BodyText size={13} color={t.colors.clay} style={{ marginTop: 12 }}>
          {error}
        </BodyText>
      )}

      <PrimaryButton
        label="Save location"
        variant="accent"
        isLoading={update.isPending}
        onPress={save}
        testID="location-save"
      />
      <View style={{ height: 8 }} />
    </ProfileSheet>
  );
}
