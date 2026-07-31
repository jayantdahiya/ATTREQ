import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { mono } from '../theme/typography';
import { AttreqIcon } from '../icons/AttreqIcon';

// Wizard step-progress nav (attreq-auth ATTREQStepNav): circular back affordance,
// dot indicators (active dot elongated), and an NN/NN counter.
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
    <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' }}>
      <Pressable
        onPress={onBack}
        accessibilityRole="button"
        accessibilityLabel="Back"
        style={{
          width: 30,
          height: 30,
          borderRadius: 100,
          borderWidth: 1,
          borderColor: t.colors.border,
          alignItems: 'center',
          justifyContent: 'center',
        }}>
        <AttreqIcon name="back" size={14} color={t.colors.t2} />
      </Pressable>
      <View style={{ flexDirection: 'row', gap: 5, alignItems: 'center' }}>
        {Array.from({ length: total }).map((_, i) => (
          <View
            key={i}
            style={{
              height: 3,
              borderRadius: 100,
              width: i === step ? 22 : 8,
              backgroundColor: i <= step ? t.colors.text : t.colors.border,
            }}
          />
        ))}
      </View>
      <Text style={[mono(9.5), { letterSpacing: 1.6, textTransform: 'uppercase', color: t.colors.t3 }]}>
        {String(step + 1).padStart(2, '0')}/{String(total).padStart(2, '0')}
      </Text>
    </View>
  );
}
