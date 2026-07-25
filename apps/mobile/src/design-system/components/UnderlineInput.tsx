import React from 'react';
import { KeyboardTypeOptions, TextInput, View } from 'react-native';
import { useTheme } from '../theme/ThemeProvider';
import { body } from '../theme/typography';
import { MonoLabel } from './MonoLabel';

// Mono uppercase label over an underline text field (attreq-shared ATTREQInput).
export function UnderlineInput({
  label,
  value,
  onChangeText,
  secureTextEntry = false,
  placeholder,
  keyboardType,
  autoCapitalize = 'none',
  testID,
}: {
  label: string;
  value: string;
  onChangeText?: (text: string) => void;
  secureTextEntry?: boolean;
  placeholder?: string;
  keyboardType?: KeyboardTypeOptions;
  autoCapitalize?: 'none' | 'sentences' | 'words' | 'characters';
  testID?: string;
}) {
  const t = useTheme();
  return (
    <View style={{ gap: 5 }}>
      <MonoLabel>{label}</MonoLabel>
      <TextInput
        value={value}
        onChangeText={onChangeText}
        secureTextEntry={secureTextEntry}
        placeholder={placeholder}
        placeholderTextColor={t.colors.t3}
        keyboardType={keyboardType}
        autoCapitalize={autoCapitalize}
        testID={testID}
        style={[
          body(14.5),
          { color: t.colors.text, borderBottomWidth: 1, borderBottomColor: t.colors.border, paddingVertical: 6 },
        ]}
      />
    </View>
  );
}
