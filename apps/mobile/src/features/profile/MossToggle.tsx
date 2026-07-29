import React from 'react';
import { Pressable, View } from 'react-native';
import { useTheme } from '@/design-system/theme/ThemeProvider';

/**
 * 36×20 moss pill toggle (artboard 08 reminder row) — moss track when on,
 * hairline border track when off, 16pt paper thumb. Mirrors the iOS MossToggle.
 */
export function MossToggle({
  isOn,
  onToggle,
  disabled = false,
  testID,
}: {
  isOn: boolean;
  onToggle: () => void;
  disabled?: boolean;
  testID?: string;
}) {
  const t = useTheme();
  return (
    <Pressable
      onPress={onToggle}
      disabled={disabled}
      accessibilityRole="switch"
      accessibilityState={{ checked: isOn, disabled }}
      accessibilityLabel="Daily reminder"
      testID={testID}
      hitSlop={12}
      style={{ opacity: disabled ? 0.5 : 1 }}>
      <View
        style={{
          width: 36,
          height: 20,
          borderRadius: 100,
          backgroundColor: isOn ? t.colors.moss : 'transparent',
          borderWidth: isOn ? 0 : 1,
          borderColor: t.colors.border,
          justifyContent: 'center',
          alignItems: isOn ? 'flex-end' : 'flex-start',
          paddingHorizontal: 2,
        }}>
        <View style={{ width: 16, height: 16, borderRadius: 100, backgroundColor: t.colors.bg }} />
      </View>
    </Pressable>
  );
}
