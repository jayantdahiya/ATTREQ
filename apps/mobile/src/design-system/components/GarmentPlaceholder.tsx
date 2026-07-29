import React from 'react';
import { StyleProp, View, ViewStyle } from 'react-native';
import Svg, { Defs, LinearGradient, Rect, Stop } from 'react-native-svg';
import { useTheme } from '../theme/ThemeProvider';
import { GarmentTone } from '../theme/theme';
import { MonoLabel } from './MonoLabel';

// Garment thumbnail placeholder — two-stop 155° gradient per tone. Uses react-native-svg
// (no expo-linear-gradient dependency at A0). Optional lower-left mono label.
export function GarmentPlaceholder({
  tone = 'top',
  label,
  radius = 14,
  style,
}: {
  tone?: GarmentTone;
  label?: string;
  radius?: number;
  style?: StyleProp<ViewStyle>;
}) {
  const t = useTheme();
  const [start, end] = t.garment[tone];
  const gid = `garment-${tone}`;
  return (
    <View style={[{ borderRadius: radius, overflow: 'hidden' }, style]}>
      <Svg width="100%" height="100%">
        <Defs>
          <LinearGradient id={gid} x1="0.27" y1="0" x2="0.73" y2="1">
            <Stop offset="0" stopColor={start} />
            <Stop offset="1" stopColor={end} />
          </LinearGradient>
        </Defs>
        <Rect x="0" y="0" width="100%" height="100%" fill={`url(#${gid})`} />
      </Svg>
      {label ? (
        <View style={{ position: 'absolute', bottom: 7, left: 8 }}>
          <MonoLabel size={7.5} color={t.colors.t3}>
            {label}
          </MonoLabel>
        </View>
      ) : null}
    </View>
  );
}
