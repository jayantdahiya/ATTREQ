import React from 'react';
import { Pressable, View } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { AttreqIcon } from '../icons/AttreqIcon';

// Wizard step-progress nav: back affordance + segmented progress bar.
export function StepNav({
  step,
  total = 3,
  onBack,
}: {
  step: number;
  total?: number;
  onBack?: () => void;
}) {
  const t = useTheme();
  return (
    <View style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
      <Pressable onPress={onBack} hitSlop={8} accessibilityRole="button" accessibilityLabel="Back">
        <AttreqIcon name="back" size={14} color={t.colors.t2} />
      </Pressable>
      <View style={{ flexDirection: 'row', gap: 6, flex: 1 }}>
        {Array.from({ length: total }).map((_, i) => (
          <View
            key={i}
            style={{
              height: 3,
              flex: 1,
              borderRadius: 2,
              backgroundColor: i <= step ? t.colors.accent : t.colors.border,
            }}
          />
        ))}
      </View>
    </View>
  );
}
