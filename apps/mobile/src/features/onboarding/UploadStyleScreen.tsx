import React from 'react';
import { Image, Pressable, Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display, mono } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { pickMultipleFromLibrary } from '@/lib/media/image-picker';
import { MAX_PHOTOS, type OnboardingController } from '@/features/onboarding/useOnboardingController';

function ErrorBanner({ message }: { message: string }) {
  const t = useTheme();
  return (
    <BodyText size={13} color={t.colors.clay} style={{ marginBottom: 12 }}>
      {message}
    </BodyText>
  );
}

export function UploadStyleScreen({
  c,
  onBuild,
  onSkip,
}: {
  c: OnboardingController;
  onBuild: () => void;
  onSkip: () => void;
}) {
  const t = useTheme();
  // 6 tiles minimum; grow to keep one empty "add" tile visible, capping at 8.
  const tileCount = Math.max(6, Math.min(MAX_PHOTOS, c.photos.length + 1));

  const pick = async () => {
    const picked = await pickMultipleFromLibrary(MAX_PHOTOS - c.photos.length);
    if (picked.length > 0) c.addPhotos(picked);
  };

  const fraction = c.photos.length / MAX_PHOTOS;

  return (
    <View testID="onboarding-upload-screen" style={{ gap: 0 }}>
      <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
        Step 01 — Upload
      </MonoLabel>
      <Text style={[display(34), { color: t.colors.text, marginBottom: 8 }]}>
        Show us{'\n'}
        <Text style={[display(34, { italic: true }), { color: t.colors.accent }]}>your style.</Text>
      </Text>
      <BodyText style={{ marginBottom: 24 }}>
        Upload 3–8 outfit photos you love. We'll read your aesthetic and pre-fill your wardrobe.
      </BodyText>

      {/* 3-column photo grid */}
      <View style={{ flexDirection: 'row', flexWrap: 'wrap', gap: 9, marginBottom: 16 }}>
        {Array.from({ length: tileCount }).map((_, index) => {
          const asset = c.photos[index];
          if (asset) {
            return (
              <View
                key={index}
                style={{ width: '31.5%', aspectRatio: 3 / 4, borderRadius: 14, overflow: 'hidden' }}>
                <Image source={{ uri: asset.uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
                <Pressable
                  onPress={() => c.removePhoto(index)}
                  disabled={c.isUploading}
                  hitSlop={8}
                  accessibilityRole="button"
                  accessibilityLabel={`Remove photo ${index + 1}`}
                  style={{
                    position: 'absolute',
                    top: 5,
                    right: 5,
                    width: 22,
                    height: 22,
                    borderRadius: 11,
                    backgroundColor: 'rgba(0,0,0,0.45)',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                  <AttreqIcon name="x" size={11} color="#FFFFFF" />
                </Pressable>
              </View>
            );
          }
          return (
            <Pressable
              key={index}
              onPress={pick}
              disabled={c.isUploading}
              testID={index === c.photos.length ? 'onboarding-pick-photos' : undefined}
              accessibilityRole="button"
              accessibilityLabel="Add photos"
              style={{
                width: '31.5%',
                aspectRatio: 3 / 4,
                borderRadius: 14,
                borderWidth: 1.5,
                borderColor: t.colors.border,
                borderStyle: 'dashed',
                alignItems: 'center',
                justifyContent: 'center',
                backgroundColor: t.colors.surface,
              }}>
              <AttreqIcon name="image" size={16} color={t.colors.t3} />
            </Pressable>
          );
        })}
      </View>

      {/* Progress */}
      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 28 }}>
        <View style={{ flex: 1, height: 3, borderRadius: 100, backgroundColor: t.colors.borderSoft }}>
          <View style={{ width: `${fraction * 100}%`, height: 3, borderRadius: 100, backgroundColor: t.colors.accent }} />
        </View>
        <MonoLabel>{c.photos.length} of {MAX_PHOTOS} photos</MonoLabel>
      </View>

      {c.uploadError ? <ErrorBanner message={c.uploadError} /> : null}
      {c.completionError ? <ErrorBanner message={c.completionError} /> : null}

      <View style={{ gap: 13 }}>
        <PrimaryButton
          label="Build my Style DNA"
          variant="accent"
          icon="chevron"
          isLoading={c.isUploading}
          disabled={!c.canBuild || c.isCompleting}
          onPress={onBuild}
          testID="onboarding-build"
        />
        {c.isUploading ? (
          <BodyText size={12} style={{ textAlign: 'center' }}>
            This takes 10–30 seconds. We're reading your aesthetic.
          </BodyText>
        ) : null}
        <Pressable
          onPress={onSkip}
          disabled={c.isUploading || c.isCompleting}
          accessibilityRole="button"
          testID="onboarding-skip"
          style={{ alignSelf: 'center', paddingVertical: 6 }}>
          <Text style={[mono(9.5), { letterSpacing: 1.2, textTransform: 'uppercase', color: t.colors.t3 }]}>
            Skip for now
          </Text>
        </Pressable>
      </View>
    </View>
  );
}
