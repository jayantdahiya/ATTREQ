import React from 'react';
import { ActivityIndicator, Pressable, Text } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { body } from '../theme/typography';
import { AttreqIcon, AttreqIconName } from '../icons/AttreqIcon';

// Full-width pill button — ink fill by default, accent (camel) variant available (attreq-shared ATTREQBtn).
export function PrimaryButton({
  label,
  onPress,
  variant = 'default',
  isLoading = false,
  disabled = false,
  icon,
  testID,
}: {
  label: string;
  onPress?: () => void;
  variant?: 'default' | 'accent';
  isLoading?: boolean;
  disabled?: boolean;
  icon?: AttreqIconName;
  testID?: string;
}) {
  const t = useTheme();
  const bg = variant === 'accent' ? t.colors.accent : t.colors.text;
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled || isLoading}
      testID={testID}
      accessibilityRole="button"
      style={{
        backgroundColor: bg,
        borderRadius: 100,
        paddingVertical: 13,
        paddingHorizontal: 24,
        flexDirection: 'row',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 6,
        width: '100%',
        opacity: disabled ? 0.5 : 1,
      }}>
      {isLoading && <ActivityIndicator size="small" color={t.colors.bg} />}
      <Text style={[body(14, 'medium'), { color: t.colors.bg, letterSpacing: 0.2 }]}>{label}</Text>
      {icon && !isLoading && <AttreqIcon name={icon} size={16} color={t.colors.bg} />}
    </Pressable>
  );
}
