import React from 'react';
import { Pressable, Text } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { body } from '../theme/typography';

// Selectable pill chip — selected fills with ink, text flips to bg (attreq-shared ATTREQChip).
export function Chip({
  label,
  selected = false,
  onPress,
  testID,
}: {
  label: string;
  selected?: boolean;
  onPress?: () => void;
  testID?: string;
}) {
  const t = useTheme();
  return (
    <Pressable
      onPress={onPress}
      testID={testID}
      accessibilityRole="button"
      accessibilityState={{ selected }}
      style={{
        paddingVertical: 6,
        paddingHorizontal: 14,
        borderRadius: 100,
        backgroundColor: selected ? t.colors.text : 'transparent',
        borderWidth: 1,
        borderColor: selected ? t.colors.text : t.colors.border,
        alignSelf: 'flex-start',
      }}>
      <Text style={[body(13, 'medium'), { color: selected ? t.colors.bg : t.colors.t2 }]}>{label}</Text>
    </Pressable>
  );
}
