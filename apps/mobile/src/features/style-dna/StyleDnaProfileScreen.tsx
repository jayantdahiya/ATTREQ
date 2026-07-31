import React, { useState } from 'react';
import { ActivityIndicator, Image, Pressable, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { UnderlineInput } from '@/design-system/components/UnderlineInput';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { StyleDnaCard } from '@/features/style-dna/StyleDnaCard';
import { useDeleteStylePhotos, useRegenerate, useStyleDna, useUpdateStyleDna } from '@/lib/query/style-dna';
import { MIN_PHOTOS } from '@/features/onboarding/useOnboardingController';
import { resolveImageUrl } from '@/lib/utils/images';
import { describeAuthError } from '@/lib/api/errors';

export function StyleDnaProfileScreen({ onBack }: { onBack: () => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { data, isLoading, isError, error, refetch, isRefetching } = useStyleDna();
  const regenerate = useRegenerate();
  const deletePhotos = useDeleteStylePhotos();
  const update = useUpdateStyleDna();

  const [editing, setEditing] = useState(false);
  const [aestheticDraft, setAestheticDraft] = useState('');

  const dna = data?.style_dna ?? null;
  const photos = data?.photos ?? [];
  const canRegenerate = photos.length >= MIN_PHOTOS;

  const actionError =
    (regenerate.error && describeAuthError(regenerate.error)) ||
    (deletePhotos.error && describeAuthError(deletePhotos.error)) ||
    (update.error && describeAuthError(update.error)) ||
    null;

  const startEdit = () => {
    setAestheticDraft(dna?.aesthetic?.primary ?? '');
    setEditing(true);
  };

  const saveEdit = () => {
    const primary = aestheticDraft.trim();
    if (!primary) {
      setEditing(false);
      return;
    }
    update.mutate(
      { corrections: { aesthetic: { primary } } },
      { onSuccess: () => setEditing(false) },
    );
  };

  const BackButton = (
    <Pressable
      onPress={onBack}
      hitSlop={10}
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
  );

  return (
    <View testID="style-dna-profile-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        contentContainerStyle={{
          paddingTop: insets.top + 12,
          paddingBottom: insets.bottom + 40,
          paddingHorizontal: 28,
          gap: 18,
        }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          {BackButton}
          <MonoLabel>Style DNA</MonoLabel>
        </View>

        {isLoading ? (
          <View style={{ marginTop: 40, alignItems: 'center', gap: 12 }}>
            <ActivityIndicator color={t.colors.t2} />
            <MonoLabel>Loading your style profile</MonoLabel>
          </View>
        ) : isError ? (
          <View style={{ marginTop: 40, gap: 16 }}>
            <MonoLabel size={11} color={t.colors.clay}>
              Something went wrong
            </MonoLabel>
            <BodyText size={13} color={t.colors.clay}>
              {describeAuthError(error)}
            </BodyText>
            <PrimaryButton label="Try again" onPress={() => void refetch()} isLoading={isRefetching} />
          </View>
        ) : (
          <>
            <Text style={[display(34), { color: t.colors.text }]}>
              Your style,{' '}
              <Text style={[display(34, { italic: true }), { color: t.colors.accent }]}>decoded.</Text>
            </Text>

            {actionError ? (
              <View style={{ padding: 12, borderRadius: 12, backgroundColor: t.colors.claySoft }}>
                <BodyText size={13} color={t.colors.clay}>
                  {actionError}
                </BodyText>
              </View>
            ) : null}

            {dna ? (
              <>
                <StyleDnaCard dna={dna} />

                {/* Lightweight PATCH affordance — edit the primary aesthetic
                    label (deep-merged server-side). */}
                {editing ? (
                  <View style={{ gap: 12 }}>
                    <UnderlineInput
                      label="Primary aesthetic"
                      value={aestheticDraft}
                      onChangeText={setAestheticDraft}
                      autoCapitalize="none"
                      testID="style-dna-edit-input"
                    />
                    <View style={{ flexDirection: 'row', gap: 12 }}>
                      <View style={{ flex: 1 }}>
                        <PrimaryButton
                          label="Save"
                          variant="accent"
                          isLoading={update.isPending}
                          onPress={saveEdit}
                          testID="style-dna-edit-save"
                        />
                      </View>
                      <View style={{ flex: 1 }}>
                        <PrimaryButton label="Cancel" onPress={() => setEditing(false)} />
                      </View>
                    </View>
                  </View>
                ) : (
                  <Pressable onPress={startEdit} accessibilityRole="button" testID="style-dna-edit">
                    <MonoLabel color={t.colors.accent}>Edit aesthetic</MonoLabel>
                  </Pressable>
                )}
              </>
            ) : (
              <View style={{ gap: 8 }}>
                <MonoLabel size={11}>No Style DNA yet</MonoLabel>
                <BodyText size={13}>
                  We'll read your aesthetic from your outfit photos and build your style profile here.
                </BodyText>
              </View>
            )}

            {/* Seed photos */}
            <View style={{ gap: 10 }}>
              <MonoLabel>Seed Photos</MonoLabel>
              <BodyText size={13}>
                Based on {photos.length} seed photo{photos.length === 1 ? '' : 's'}.
              </BodyText>
              {photos.length > 0 ? (
                <>
                  <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 9 }}>
                    {photos.map((photo) => {
                      const uri = resolveImageUrl(photo.file_url);
                      return (
                        <View
                          key={photo.id}
                          testID={`style-dna-photo-${photo.id}`}
                          style={{
                            width: '31.5%',
                            aspectRatio: 3 / 4,
                            borderRadius: 14,
                            overflow: 'hidden',
                            backgroundColor: t.colors.surface,
                            borderWidth: 1,
                            borderColor: t.colors.border,
                            opacity: deletePhotos.isPending ? 0.45 : 1,
                          }}>
                          {uri ? (
                            <Image source={{ uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
                          ) : null}
                        </View>
                      );
                    })}
                  </View>
                  <Pressable
                    onPress={() => deletePhotos.mutate()}
                    disabled={deletePhotos.isPending}
                    accessibilityRole="button"
                    testID="style-dna-remove-photos"
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      justifyContent: 'center',
                      gap: 6,
                      paddingVertical: 11,
                      borderRadius: 100,
                      borderWidth: 1,
                      borderColor: t.colors.border,
                    }}>
                    <AttreqIcon name="x" size={12} color={t.colors.clay} />
                    <Text style={{ color: t.colors.clay, fontSize: 13, fontWeight: '500' }}>
                      {deletePhotos.isPending ? 'Removing…' : 'Remove all photos'}
                    </Text>
                  </Pressable>
                </>
              ) : null}
            </View>

            {canRegenerate ? (
              <PrimaryButton
                label="Regenerate Style DNA"
                variant="accent"
                isLoading={regenerate.isPending}
                onPress={() => regenerate.mutate()}
                testID="style-dna-regenerate"
              />
            ) : (
              <MonoLabel size={9}>Regenerate needs 3+ stored photos</MonoLabel>
            )}
          </>
        )}
      </ScrollView>
    </View>
  );
}
