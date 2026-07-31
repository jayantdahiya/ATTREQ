import React from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { body, display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import type { WeatherData } from '@/lib/api/types';

/**
 * Compact weather strip under the Today header. City comes from the user
 * profile (saved_city / location), not the weather payload. Degrades keyless
 * (no OPENWEATHER key): `weather == null` renders "—" for temp and condition.
 */
export function WeatherStrip({ city, weather }: { city: string | null; weather: WeatherData | null | undefined }) {
  const t = useTheme();
  const cityText = city && city.length > 0 ? city : '—';
  const tempText = weather ? `${Math.round(weather.temp)}°` : '—';

  return (
    <View
      testID="weather-strip"
      style={{
        flexDirection: 'row',
        alignItems: 'center',
        borderRadius: 14,
        borderWidth: 1,
        borderColor: t.colors.border,
        backgroundColor: t.colors.surface,
        paddingVertical: 11,
        paddingHorizontal: 14,
      }}>
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6, flexShrink: 1 }}>
        <AttreqIcon name="location" size={12} color={t.colors.t3} />
        <Text numberOfLines={1} style={[body(13), { color: t.colors.t2 }]}>
          {cityText}
        </Text>
      </View>
      <View style={{ flex: 1 }} />
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
        <Text style={[display(20), { color: t.colors.text }]}>{tempText}</Text>
        <View style={{ width: 1, height: 14, backgroundColor: t.colors.border }} />
        <MonoLabel>{weather?.condition ?? '—'}</MonoLabel>
      </View>
    </View>
  );
}
