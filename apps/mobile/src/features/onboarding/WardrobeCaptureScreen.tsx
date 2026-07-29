import React, { useEffect } from 'react';
import { Image, Pressable, ScrollView, Text, View } from 'react-native';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { AttreqIcon, type AttreqIconName } from '@/design-system/icons/AttreqIcon';
import { pickFromCamera, pickMultipleFromLibrary } from '@/lib/media/image-picker';
import { MAX_CAPTURE_PHOTOS, type OnboardingController } from '@/features/onboarding/useOnboardingController';

const LIBRARY_MIN = 10;
const LIBRARY_MAX = 20;

function CaptureTile({
  icon,
  label,
  sublabel,
  disabled,
  onPress,
  testID,
}: {
  icon: AttreqIconName;
  label: string;
  sublabel: string;
  disabled: boolean;
  onPress: () => void;
  testID: string;
}) {
  const t = useTheme();
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      testID={testID}
      accessibilityRole="button"
      style={{
        flex: 1,
        borderRadius: 14,
        borderWidth: 1.5,
        borderColor: t.colors.border,
        borderStyle: 'dashed',
        backgroundColor: t.colors.surface,
        paddingVertical: 12,
        paddingHorizontal: 13,
        gap: 5,
        opacity: disabled ? 0.45 : 1,
      }}>
      <View
        style={{
          width: 28,
          height: 28,
          borderRadius: 14,
          backgroundColor: t.colors.accentSoft,
          alignItems: 'center',
          justifyContent: 'center',
        }}>
        <AttreqIcon name={icon} size={13} color={t.colors.t2} />
      </View>
      <Text style={{ color: t.colors.text, fontSize: 13, fontWeight: '500' }}>{label}</Text>
      <MonoLabel>{sublabel}</MonoLabel>
    </Pressable>
  );
}

export function WardrobeCaptureScreen({ c, onFinish }: { c: OnboardingController; onFinish: () => void }) {
  const t = useTheme();
  const atCap = c.capturePhotos.length >= MAX_CAPTURE_PHOTOS;

  useEffect(() => {
    void c.refreshWardrobeCount();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const captureFromCamera = async () => {
    const asset = await pickFromCamera();
    if (asset) c.addCapturePhotos([asset]);
  };

  const pickFromLibrary = async () => {
    const picked = await pickMultipleFromLibrary(MAX_CAPTURE_PHOTOS - c.capturePhotos.length);
    if (picked.length > 0) c.addCapturePhotos(picked);
  };

  const progressLine =
    c.itemsRemaining > 0
      ? `${c.wardrobeItemCount} items added — ${c.itemsRemaining} more unlocks better matches`
      : `${c.wardrobeItemCount} items added — plenty for great matches`;

  return (
    <View testID="capture-screen" style={{ gap: 0 }}>
      <MonoLabel color={t.colors.accent} style={{ marginBottom: 8 }}>
        Step 04 — Wardrobe
      </MonoLabel>
      <Text style={[display(34), { color: t.colors.text, marginBottom: 8 }]}>
        Build your{'\n'}
        <Text style={[display(34, { italic: true }), { color: t.colors.accent }]}>wardrobe.</Text>
      </Text>

      <View style={{ padding: 14, borderRadius: 16, backgroundColor: t.colors.accentSoft, gap: 8, marginBottom: 20 }}>
        {[
          'Roughly a quarter of the average closet is never worn.',
          'We only ever recommend outfits from clothes you already own — no ads, no affiliate picks.',
        ].map((fact) => (
          <View key={fact} style={{ flexDirection: 'row', gap: 8 }}>
            <AttreqIcon name="sparkles" size={12} color={t.colors.accent} />
            <BodyText size={13} color={t.colors.text} style={{ flex: 1 }}>
              {fact}
            </BodyText>
          </View>
        ))}
      </View>

      {c.capturePhotos.length > 0 ? (
        <View style={{ gap: 8, marginBottom: 16 }}>
          <MonoLabel>
            {c.capturePhotos.length} piece{c.capturePhotos.length === 1 ? '' : 's'} captured
          </MonoLabel>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
            {c.capturePhotos.map((asset, index) => (
              <View key={index} style={{ width: 72, height: 90, borderRadius: 14, overflow: 'hidden' }}>
                <Image source={{ uri: asset.uri }} style={{ width: '100%', height: '100%' }} resizeMode="cover" />
                <Pressable
                  onPress={() => c.removeCapturePhoto(index)}
                  disabled={c.captureState === 'uploading'}
                  hitSlop={8}
                  accessibilityRole="button"
                  accessibilityLabel={`Remove photo ${index + 1}`}
                  style={{
                    position: 'absolute',
                    top: 4,
                    right: 4,
                    width: 18,
                    height: 18,
                    borderRadius: 9,
                    backgroundColor: 'rgba(0,0,0,0.45)',
                    alignItems: 'center',
                    justifyContent: 'center',
                  }}>
                  <AttreqIcon name="x" size={9} color="#FFFFFF" />
                </Pressable>
              </View>
            ))}
          </ScrollView>
        </View>
      ) : null}

      <View style={{ flexDirection: 'row', gap: 9, marginBottom: 16 }}>
        <CaptureTile
          icon="camera"
          label="Camera"
          sublabel="One piece at a time"
          disabled={atCap}
          onPress={captureFromCamera}
          testID="capture-camera"
        />
        <CaptureTile
          icon="image"
          label="Library"
          sublabel={`Pick ${LIBRARY_MIN}–${LIBRARY_MAX} at once`}
          disabled={atCap}
          onPress={pickFromLibrary}
          testID="capture-library"
        />
      </View>

      <MonoLabel size={9} style={{ marginBottom: 12 }}>
        {progressLine}
      </MonoLabel>

      {c.captureState === 'failed' && c.captureError ? (
        <BodyText size={13} color={t.colors.clay} style={{ marginBottom: 12 }}>
          {c.captureError}
        </BodyText>
      ) : null}
      {c.captureState === 'done' ? (
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 }}>
          <AttreqIcon name="check" size={14} color={t.colors.moss} />
          <BodyText size={13} color={t.colors.moss}>
            Added to your wardrobe.
          </BodyText>
        </View>
      ) : null}

      <View style={{ gap: 13, marginTop: 16 }}>
        {c.capturePhotos.length > 0 ? (
          <PrimaryButton
            label={`Add ${c.capturePhotos.length} to wardrobe`}
            variant="accent"
            isLoading={c.captureState === 'uploading'}
            onPress={() => void c.uploadCapturePhotos()}
            testID="capture-upload"
          />
        ) : null}
        <PrimaryButton
          label="Continue"
          icon="chevron"
          isLoading={c.isCompleting}
          disabled={c.captureState === 'uploading'}
          onPress={onFinish}
          testID="capture-continue"
        />
      </View>
    </View>
  );
}
