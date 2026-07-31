import React, { useEffect } from 'react';
import { BackHandler, Modal, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { body } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';

/**
 * Shared bottom-sheet shell for the Profile edit modals (location, style
 * preferences, change password, delete account). Mirrors the RejectionReasonSheet
 * Modal pattern: translucent scrim, rounded top, hardware-back + onRequestClose
 * both dismiss (`onClose`). Content scrolls inside.
 */
export function ProfileSheet({
  visible,
  onClose,
  headerLabel,
  testID,
  children,
}: {
  visible: boolean;
  onClose: () => void;
  headerLabel: string;
  testID?: string;
  children: React.ReactNode;
}) {
  const t = useTheme();
  const insets = useSafeAreaInsets();

  useEffect(() => {
    if (!visible) return;
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      onClose();
      return true;
    });
    return () => sub.remove();
  }, [visible, onClose]);

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.35)', justifyContent: 'flex-end' }}>
        <View
          testID={testID}
          style={{
            backgroundColor: t.colors.bg,
            borderTopLeftRadius: 28,
            borderTopRightRadius: 28,
            maxHeight: '90%',
            paddingBottom: insets.bottom + 24,
          }}>
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingHorizontal: 28,
              paddingTop: 22,
              paddingBottom: 8,
            }}>
            <MonoLabel color={t.colors.accent}>{headerLabel}</MonoLabel>
            <Text
              onPress={onClose}
              accessibilityRole="button"
              testID="sheet-close"
              style={[body(13, 'medium'), { color: t.colors.t2 }]}>
              Close
            </Text>
          </View>
          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 28, paddingTop: 8 }}>
            {children}
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}
