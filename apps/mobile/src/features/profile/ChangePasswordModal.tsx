import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import { ProfileSheet } from '@/features/profile/ProfileSheet';
import { useChangePassword } from '@/lib/query/users';
import { describeAuthError } from '@/lib/api/errors';

/**
 * Change-password editor (Profile). POST /users/change-password. Client mirrors
 * the backend PasswordChange rules (>=8 chars, one upper, one lower, one digit)
 * plus a confirm field, so obvious mistakes are caught before the round-trip.
 */
export function ChangePasswordModal({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const t = useTheme();
  const change = useChangePassword();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [confirm, setConfirm] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  useEffect(() => {
    if (visible) {
      setCurrent('');
      setNext('');
      setConfirm('');
      setError(null);
      setDone(false);
    }
  }, [visible]);

  const validate = (): string | null => {
    if (current.length === 0) return 'Enter your current password.';
    if (next.length < 8) return 'New password must be at least 8 characters.';
    if (!/[A-Z]/.test(next)) return 'New password needs an uppercase letter.';
    if (!/[a-z]/.test(next)) return 'New password needs a lowercase letter.';
    if (!/[0-9]/.test(next)) return 'New password needs a digit.';
    if (next !== confirm) return "New passwords don't match.";
    return null;
  };

  const save = () => {
    const problem = validate();
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    change.mutate(
      { current_password: current, new_password: next },
      {
        onSuccess: () => {
          setDone(true);
          setTimeout(onClose, 900);
        },
        onError: (e) => setError(describeAuthError(e)),
      },
    );
  };

  return (
    <ProfileSheet visible={visible} onClose={onClose} headerLabel="Account — Password" testID="password-sheet">
      <Text style={[display(26), { color: t.colors.text, marginBottom: 6 }]}>Update your password.</Text>
      <BodyText size={13} style={{ marginBottom: 20 }}>
        At least 8 characters with an uppercase letter, a lowercase letter, and a digit.
      </BodyText>

      <Card padding={20}>
        <View style={{ gap: 16 }}>
          <UnderlineInput
            label="Current password"
            value={current}
            onChangeText={setCurrent}
            secureTextEntry
            testID="password-current"
          />
          <UnderlineInput
            label="New password"
            value={next}
            onChangeText={setNext}
            secureTextEntry
            testID="password-new"
          />
          <UnderlineInput
            label="Confirm new password"
            value={confirm}
            onChangeText={setConfirm}
            secureTextEntry
            testID="password-confirm"
          />
        </View>
      </Card>

      {error && (
        <BodyText size={13} color={t.colors.clay} style={{ marginTop: 12 }}>
          {error}
        </BodyText>
      )}
      {done && (
        <BodyText size={13} color={t.colors.moss} style={{ marginTop: 12 }}>
          Password updated.
        </BodyText>
      )}

      <PrimaryButton
        label="Update password"
        variant="accent"
        isLoading={change.isPending}
        onPress={save}
        testID="password-save"
      />
      <View style={{ height: 8 }} />
    </ProfileSheet>
  );
}
