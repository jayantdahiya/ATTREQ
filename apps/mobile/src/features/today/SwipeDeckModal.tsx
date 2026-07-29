import React, { useEffect, useState } from 'react';
import { ActivityIndicator, BackHandler, Modal, Pressable, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { AxiosError } from 'axios';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { display } from '@/design-system/theme/typography';
import { Card } from '@/design-system/components/Card';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';
import { GarmentCollage } from '@/features/today/GarmentCollage';
import { recommendationsApi } from '@/lib/api/recommendations';
import { useSwipeDeck } from '@/lib/query/recommendations';
import { describeAuthError } from '@/lib/api/errors';

/**
 * "Rate a few looks" swipe deck (RN Modal). A short, optional deck of freshly-
 * generated outfits rated thumbs up/down — each rating submits through the same
 * recommendation-feedback endpoint as the Today card (accepted/rejected). No
 * outfit row is created. Closable at any point; a 429 (daily cap) is a quiet,
 * factual state, never a failure banner.
 */
export function SwipeDeckModal({ visible, onClose }: { visible: boolean; onClose: () => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const deck = useSwipeDeck(visible);
  const [index, setIndex] = useState(0);
  const [exhausted, setExhausted] = useState(false);
  const [capReached, setCapReached] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (visible) {
      setIndex(0);
      setExhausted(false);
      setCapReached(false);
      setIsSubmitting(false);
      setErrorMessage(null);
    }
  }, [visible]);

  useEffect(() => {
    if (!visible) return;
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      onClose();
      return true;
    });
    return () => sub.remove();
  }, [visible, onClose]);

  const suggestions = deck.data?.suggestions ?? [];
  const recommendationId = deck.data?.recommendation_id;
  const current = !exhausted && index < suggestions.length ? suggestions[index] : undefined;
  const notFound = (deck.error as AxiosError | undefined)?.response?.status === 404;

  const rate = async (liked: boolean) => {
    if (!current || !recommendationId || isSubmitting) return;
    setIsSubmitting(true);
    try {
      await recommendationsApi.submitFeedback(recommendationId, {
        outfit_index: current.outfit_index,
        action: liked ? 'accepted' : 'rejected',
      });
      setErrorMessage(null);
      if (index >= suggestions.length - 1) setExhausted(true);
      else setIndex((i) => i + 1);
    } catch (error) {
      const status = (error as AxiosError | undefined)?.response?.status;
      if (status === 429) setCapReached(true);
      else setErrorMessage(describeAuthError(error));
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose} statusBarTranslucent>
      <View
        testID="swipe-deck"
        style={{
          flex: 1,
          backgroundColor: t.colors.bg,
          paddingTop: insets.top + 20,
          paddingBottom: insets.bottom + 24,
          paddingHorizontal: 24,
        }}>
        {/* Header */}
        <View style={{ flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', marginBottom: 18 }}>
          <View style={{ gap: 3 }}>
            <Text style={[display(20, { italic: true }), { color: t.colors.text }]}>Rate a few looks</Text>
            {deck.isSuccess && suggestions.length > 0 && !exhausted && (
              <MonoLabel>{`${index + 1} of ${suggestions.length}`}</MonoLabel>
            )}
          </View>
          <Pressable
            onPress={onClose}
            accessibilityRole="button"
            accessibilityLabel="Close"
            testID="swipe-deck-close"
            style={{
              width: 34,
              height: 34,
              borderRadius: 999,
              borderWidth: 1,
              borderColor: t.colors.border,
              alignItems: 'center',
              justifyContent: 'center',
            }}>
            <AttreqIcon name="x" size={13} color={t.colors.t2} />
          </Pressable>
        </View>

        {deck.isLoading ? (
          <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
            <ActivityIndicator color={t.colors.t2} />
          </View>
        ) : deck.isError && !notFound ? (
          <Card padding={16}>
            <BodyText size={13} color={t.colors.clay}>
              {describeAuthError(deck.error)}
            </BodyText>
            <View style={{ marginTop: 14 }}>
              <PrimaryButton label="Try again" onPress={() => deck.refetch()} />
            </View>
          </Card>
        ) : !current ? (
          <Card padding={16}>
            <View style={{ gap: 10 }}>
              <MonoLabel size={11}>All set</MonoLabel>
              <BodyText size={13}>
                Thanks for rating today's looks — they'll help sharpen tomorrow's picks.
              </BodyText>
              <View style={{ marginTop: 6 }}>
                <PrimaryButton label="Close" onPress={onClose} />
              </View>
            </View>
          </Card>
        ) : (
          <Card padding={16}>
            <View style={{ marginBottom: 12 }}>
              <GarmentCollage suggestion={current} layout="deck" />
            </View>
            <View style={{ flexDirection: 'row', gap: 10, marginBottom: 16 }}>
              <MonoLabel>{`${Math.round(current.weather_context.temp)}°C — ${current.weather_context.condition}`}</MonoLabel>
              <MonoLabel color={t.colors.accent}>{`— ${current.occasion_context}`}</MonoLabel>
            </View>

            {capReached ? (
              <View style={{ gap: 8 }}>
                <MonoLabel size={10}>Cap reached for today</MonoLabel>
                <BodyText size={13}>You've rated the max looks for today — come back tomorrow for more.</BodyText>
              </View>
            ) : (
              <View style={{ flexDirection: 'row', gap: 12 }}>
                <Pressable
                  onPress={() => rate(false)}
                  disabled={isSubmitting}
                  accessibilityRole="button"
                  accessibilityLabel="Not for me"
                  testID="swipe-deck-dislike"
                  style={{
                    flex: 1,
                    paddingVertical: 14,
                    borderRadius: 14,
                    alignItems: 'center',
                    backgroundColor: t.colors.claySoft,
                    opacity: isSubmitting ? 0.6 : 1,
                  }}>
                  <AttreqIcon name="thumbsDown" size={18} color={t.colors.clay} />
                </Pressable>
                <Pressable
                  onPress={() => rate(true)}
                  disabled={isSubmitting}
                  accessibilityRole="button"
                  accessibilityLabel="Like this"
                  testID="swipe-deck-like"
                  style={{
                    flex: 1,
                    paddingVertical: 14,
                    borderRadius: 14,
                    alignItems: 'center',
                    backgroundColor: t.colors.mossSoft,
                    opacity: isSubmitting ? 0.6 : 1,
                  }}>
                  <AttreqIcon name="thumbsUp" size={18} color={t.colors.moss} />
                </Pressable>
              </View>
            )}

            {errorMessage && (
              <BodyText size={12} color={t.colors.clay} style={{ marginTop: 8 }}>
                {errorMessage}
              </BodyText>
            )}
          </Card>
        )}
      </View>
    </Modal>
  );
}
