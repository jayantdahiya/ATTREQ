import React, { useEffect, useState } from 'react';
import { Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { BodyText } from '@/design-system/components/BodyText';
import { Card } from '@/design-system/components/Card';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import { ProfileSheet } from '@/features/profile/ProfileSheet';
import { useDeleteAccount } from '@/lib/query/users';
import { describeAuthError } from '@/lib/api/errors';
import { useAuthStore } from '@/store/auth-store';

const CONFIRM_WORD = 'DELETE';

/**
 * Delete-account confirmation (Profile danger zone). DELETE /users/me
 * soft-deactivates the account (is_active=false); on success we sign out
 * immediately since the token now belongs to an inactive user. A typed-"DELETE"
 * gate guards the irreversible action.
 */
export function DeleteAccountModal({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const t = useTheme();
  const del = useDeleteAccount();
  const signOut = useAuthStore((s) => s.signOut);
  const [confirmText, setConfirmText] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (visible) {
      setConfirmText('');
      setError(null);
    }
  }, [visible]);

  const canDelete = confirmText.trim().toUpperCase() === CONFIRM_WORD;

  const confirmDelete = () => {
    if (!canDelete) {
      setError(`Type ${CONFIRM_WORD} to confirm.`);
      return;
    }
    setError(null);
    del.mutate(undefined, {
      onSuccess: () => {
        // Sign out drops the token + clears caches, returning to the login gate.
        void signOut();
      },
      onError: (e) => setError(describeAuthError(e)),
    });
  };

  return (
    <ProfileSheet visible={visible} onClose={onClose} headerLabel="Account — Delete" testID="delete-account-sheet">
      <Text style={[display(26), { color: t.colors.text, marginBottom: 6 }]}>Delete your account.</Text>
      <BodyText size={13} style={{ marginBottom: 20 }}>
        This deactivates your account and signs you out. Your wardrobe and history are retained but you'll lose access.
        Type <Text style={{ color: t.colors.clay, fontWeight: '600' }}>{CONFIRM_WORD}</Text> to confirm.
      </BodyText>

      <Card padding={20}>
        <UnderlineInput
          label={`Type ${CONFIRM_WORD}`}
          value={confirmText}
          onChangeText={setConfirmText}
          autoCapitalize="characters"
          testID="delete-confirm-input"
        />
      </Card>

      {error && (
        <BodyText size={13} color={t.colors.clay} style={{ marginTop: 12 }}>
          {error}
        </BodyText>
      )}

      <View style={{ marginTop: 4 }}>
        <PrimaryButton
          label={del.isPending ? 'Deleting…' : 'Delete account'}
          isLoading={del.isPending}
          disabled={!canDelete}
          onPress={confirmDelete}
          testID="delete-account-confirm"
        />
      </View>
      <MonoLabel size={9} color={t.colors.t3} style={{ textAlign: 'center', marginTop: 12 }}>
        This can't be undone from the app
      </MonoLabel>
      <View style={{ height: 8 }} />
    </ProfileSheet>
  );
}
