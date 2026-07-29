import React, { useEffect, useRef, useState } from 'react';
import { BackHandler, Modal, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { body, display } from '@/design-system/theme/typography';
import { Card } from '@/design-system/components/Card';
import { Chip } from '@/design-system/components/Chip';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import type { RejectionReason } from '@/lib/api/types';

// 6 of the 7 backend RejectionReason values get a chip; `other` has no chip
// and is sent implicitly when the user types a note without picking one.
const CHIP_REASONS: { key: RejectionReason; label: string }[] = [
  { key: 'too_formal', label: 'Too formal' },
  { key: 'too_casual', label: 'Too casual' },
  { key: 'dont_like_combo', label: "Don't like the combo" },
  { key: 'weather_wrong', label: 'Wrong for the weather' },
  { key: 'wore_recently', label: 'Wore this recently' },
  { key: 'dislike_item', label: 'Dislike an item' },
];

/**
 * Rejection-reason sheet (RN Modal). Skippable end-to-end: the header "Skip"
 * button, the hardware back button, and swipe-away all fire `onSubmit(null,
 * null)` — a bare rejection is still a valid preference-pair signal. `onSubmit`
 * fires EXACTLY ONCE per presentation (`submittedRef` guards both exit paths).
 */
export function RejectionReasonSheet({
  visible,
  onSubmit,
}: {
  visible: boolean;
  onSubmit: (reason: RejectionReason | null, note: string | null) => void;
}) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const [selected, setSelected] = useState<RejectionReason | null>(null);
  const [note, setNote] = useState('');
  const submittedRef = useRef(false);

  // Reset per presentation.
  useEffect(() => {
    if (visible) {
      submittedRef.current = false;
      setSelected(null);
      setNote('');
    }
  }, [visible]);

  const submit = (reason: RejectionReason | null, noteText: string | null) => {
    if (submittedRef.current) return;
    submittedRef.current = true;
    const trimmed = noteText?.trim();
    onSubmit(reason, trimmed && trimmed.length > 0 ? trimmed : null);
  };

  // A tapped-Submit with no chip but a typed note implies `other`.
  const submitFromButton = () => {
    const trimmed = note.trim();
    const reason = selected ?? (trimmed.length > 0 ? 'other' : null);
    submit(reason, note);
  };

  const bareDismiss = () => submit(null, null);

  // Wire the hardware back button while the sheet is up (Modal.onRequestClose
  // also covers it; the guard makes the redundancy harmless).
  useEffect(() => {
    if (!visible) return;
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      bareDismiss();
      return true;
    });
    return () => sub.remove();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [visible]);

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={bareDismiss}
      statusBarTranslucent>
      <View style={{ flex: 1, backgroundColor: 'rgba(0,0,0,0.35)', justifyContent: 'flex-end' }}>
        <View
          testID="rejection-sheet"
          style={{
            backgroundColor: t.colors.bg,
            borderTopLeftRadius: 28,
            borderTopRightRadius: 28,
            maxHeight: '88%',
            paddingBottom: insets.bottom + 24,
          }}>
          {/* Header */}
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              justifyContent: 'space-between',
              paddingHorizontal: 28,
              paddingTop: 22,
              paddingBottom: 16,
            }}>
            <MonoLabel>Why skip this?</MonoLabel>
            <Text
              onPress={bareDismiss}
              accessibilityRole="button"
              testID="button-Skip"
              style={[body(13, 'medium'), { color: t.colors.t2 }]}>
              Skip
            </Text>
          </View>

          <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={{ paddingHorizontal: 28 }}>
            {/* Headline */}
            <View style={{ marginBottom: 18 }}>
              <Text style={[display(30), { color: t.colors.text }]}>Help us</Text>
              <Text style={[display(30, { italic: true }), { color: t.colors.accent }]}>weave better.</Text>
            </View>

            {/* Reason card */}
            <Card padding={18} style={{ marginBottom: 20 }}>
              <View style={{ gap: 10 }}>
                <MonoLabel>Reason (optional)</MonoLabel>
                <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 6 }}>
                  {CHIP_REASONS.map((r) => (
                    <Chip
                      key={r.key}
                      label={r.label}
                      testID={`reason-${r.key}`}
                      selected={selected === r.key}
                      onPress={() => setSelected((cur) => (cur === r.key ? null : r.key))}
                    />
                  ))}
                </View>
              </View>
              <View style={{ height: 1, backgroundColor: t.colors.borderSoft, marginVertical: 16 }} />
              <UnderlineInput
                label="Add a note (optional)"
                value={note}
                onChangeText={setNote}
                autoCapitalize="sentences"
              />
            </Card>

            <PrimaryButton label="Submit" variant="accent" onPress={submitFromButton} testID="rejection-submit" />
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}
