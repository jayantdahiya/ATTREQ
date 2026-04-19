import { useState } from 'react'
import { TextInput, View, type TextInputProps } from 'react-native'

import { Text } from '@/components/ui/text'
import { cn } from '@/lib/utils/cn'
import { useThemeColors } from '@/theme/colors'

interface InputProps extends TextInputProps {
  label: string
  error?: string
}

export function Input({ className, error, label, onBlur, onFocus, ...props }: InputProps) {
  const { colors } = useThemeColors()
  const [focused, setFocused] = useState(false)

  return (
    <View>
      <Text className="mb-2" color="textTertiary" preset="label">
        {label}
      </Text>
      <TextInput
        className={cn('min-h-12 rounded-2xl border px-4 py-3', className)}
        onBlur={(event) => {
          setFocused(false)
          onBlur?.(event)
        }}
        onFocus={(event) => {
          setFocused(true)
          onFocus?.(event)
        }}
        placeholderTextColor={colors.textTertiary}
        style={{
          backgroundColor: colors.bgSurface,
          borderColor: error ? colors.accentClay : focused ? colors.accentMoss : colors.borderSubtle,
          color: colors.textPrimary,
          shadowColor: focused ? colors.accentMoss : 'transparent',
          shadowOpacity: focused ? 0.18 : 0,
          shadowRadius: 10,
          shadowOffset: { width: 0, height: 4 },
        }}
        {...props}
      />
      {error ? (
        <Text className="mt-2" color="accentClay" preset="caption">
          {error}
        </Text>
      ) : null}
    </View>
  )
}
