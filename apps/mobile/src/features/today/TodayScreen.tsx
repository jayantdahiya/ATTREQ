import React, { useEffect, useMemo, useRef, useState } from 'react';
import { ActivityIndicator, Pressable, RefreshControl, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import type { AxiosError } from 'axios';

import { useTheme } from '@/design-system/theme/ThemeProvider';
import { body, display, mono } from '@/design-system/theme/typography';
import { Card } from '@/design-system/components/Card';
import { MonoLabel } from '@/design-system/components/MonoLabel';
import { BodyText } from '@/design-system/components/BodyText';
import { Chip } from '@/design-system/components/Chip';
import { PrimaryButton } from '@/design-system/components/PrimaryButton';
import { AttreqIcon } from '@/design-system/icons/AttreqIcon';

import { WeatherStrip } from '@/features/today/WeatherStrip';
import { RecommendationCard } from '@/features/today/RecommendationCard';
import { RejectionReasonSheet } from '@/features/today/RejectionReasonSheet';
import { SwipeDeckModal } from '@/features/today/SwipeDeckModal';
import { lookTitle } from '@/features/today/lookTitles';

import { useDailySuggestions, useSwipeDeckStatus } from '@/lib/query/recommendations';
import { recommendationsApi } from '@/lib/api/recommendations';
import { outfitsApi, outfitPayloadFromSuggestion, suggestionOutfitKey } from '@/lib/api/outfits';
import { queryClient, queryKeys } from '@/lib/query/query-client';
import { getCachedUser } from '@/store/auth-store';
import { dateLine, firstName, greeting, todayLocalISO } from '@/lib/utils/dates';
import { describeAuthError } from '@/lib/api/errors';
import type { OutfitSuggestion, RejectionReason } from '@/lib/api/types';

const OCCASION = 'casual';

// Create-or-reuse map: one outfit row per suggestion per generation batch.
// Module-level so it survives re-renders (and tab-switch remounts within a
// session). Keyed by recommendation_id:top:bottom:fullbody.
const outfitDedupe = new Map<string, string>();

// Morning-vibe answer, remembered per LOCAL day for this app session (a wrong
// guess only costs a redundant prompt — no need to persist to disk).
const sessionVibe: { day: string | null; hint: string | null } = { day: null, hint: null };

const VIBES: { label: string; hint: string }[] = [
  { label: 'Sharp', hint: 'sharp' },
  { label: 'Relaxed', hint: 'relaxed' },
  { label: 'Bold', hint: 'bold' },
];

type Pending = 'skip' | 'dismiss' | null;

export function TodayScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const user = getCachedUser();

  const today = todayLocalISO();
  const [vibeHint, setVibeHint] = useState<string | null>(sessionVibe.day === today ? sessionVibe.hint : null);
  const [vibeAnswered, setVibeAnswered] = useState(sessionVibe.day === today);

  const daily = useDailySuggestions(OCCASION, vibeHint);
  const swipeStatus = useSwipeDeckStatus();

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isWearing, setIsWearing] = useState(false);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const [rejectionVisible, setRejectionVisible] = useState(false);
  const pendingRef = useRef<Pending>(null);
  const [swipeVisible, setSwipeVisible] = useState(false);

  const data = daily.data;
  const recommendationId = data?.recommendation_id;
  const suggestions = useMemo(() => data?.suggestions ?? [], [data]);

  // Reset the card to the top of a freshly-generated batch.
  useEffect(() => {
    setCurrentIndex(0);
  }, [recommendationId]);

  const current: OutfitSuggestion | undefined = suggestions[currentIndex];
  const errStatus = (daily.error as AxiosError | undefined)?.response?.status;
  const isEmpty = (daily.isSuccess && suggestions.length === 0) || errStatus === 404;
  const isFailed = daily.isError && errStatus !== 404;

  const city = user?.saved_city ?? user?.location ?? null;
  const showVibe = !vibeAnswered;
  const showSwipeEntry = swipeStatus.data ? swipeStatus.data.ratings_today < swipeStatus.data.cap : true;

  // ── Actions ────────────────────────────────────────────────────────────

  const advance = () => {
    if (suggestions.length === 0) return;
    setCurrentIndex((i) => (i + 1) % suggestions.length);
  };

  const persistOutfitId = async (suggestion: OutfitSuggestion): Promise<string> => {
    const key = suggestionOutfitKey(recommendationId ?? '-', suggestion);
    const existing = outfitDedupe.get(key);
    if (existing) return existing;
    const outfit = await outfitsApi.create(outfitPayloadFromSuggestion(suggestion));
    outfitDedupe.set(key, outfit.id);
    return outfit.id;
  };

  // Recommendation-level telemetry — fire-and-forget; never blocks/surfaces.
  const fireRecommendationFeedback = (
    suggestion: OutfitSuggestion,
    action: 'accepted' | 'rejected',
    reason?: RejectionReason | null,
    note?: string | null,
  ) => {
    if (!recommendationId) return;
    recommendationsApi
      .submitFeedback(recommendationId, {
        outfit_index: suggestion.outfit_index,
        action,
        rejection_reason: reason ?? undefined,
        rejection_note: note ?? undefined,
      })
      .catch(() => {
        /* fire-and-forget */
      });
  };

  const onWear = async () => {
    if (!current || isWearing || isSubmittingFeedback) return;
    setIsWearing(true);
    try {
      const outfitId = await persistOutfitId(current);
      await outfitsApi.markWorn(outfitId, todayLocalISO());
      setErrorMessage(null);
      fireRecommendationFeedback(current, 'accepted');
      queryClient.invalidateQueries({ queryKey: queryKeys.outfits });
      advance();
    } catch (error) {
      setErrorMessage(describeAuthError(error));
    } finally {
      setIsWearing(false);
    }
  };

  const onLove = async () => {
    if (!current || isWearing || isSubmittingFeedback) return;
    setIsSubmittingFeedback(true);
    try {
      const outfitId = await persistOutfitId(current);
      await outfitsApi.submitFeedback(outfitId, 1);
      setErrorMessage(null);
      // Love does NOT advance — the card stays put (RN parity).
    } catch (error) {
      setErrorMessage(describeAuthError(error));
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const onSkip = () => {
    if (!current) return;
    pendingRef.current = 'skip';
    setRejectionVisible(true);
  };

  const onDismiss = () => {
    if (!current) return;
    pendingRef.current = 'dismiss';
    setRejectionVisible(true);
  };

  const onRejectionSubmit = async (reason: RejectionReason | null, note: string | null) => {
    const pending = pendingRef.current;
    pendingRef.current = null;
    setRejectionVisible(false);
    const suggestion = current;
    if (!pending || !suggestion) return;

    if (pending === 'skip') {
      fireRecommendationFeedback(suggestion, 'rejected', reason, note);
      advance();
      return;
    }

    // dismiss: outfit-level -1 (creates a row → shows as "Skipped" in History)
    // plus the recommendation-level rejected signal.
    setIsSubmittingFeedback(true);
    try {
      const outfitId = await persistOutfitId(suggestion);
      await outfitsApi.submitFeedback(outfitId, -1);
      setErrorMessage(null);
      fireRecommendationFeedback(suggestion, 'rejected', reason, note);
      queryClient.invalidateQueries({ queryKey: queryKeys.outfits });
      advance();
    } catch (error) {
      setErrorMessage(describeAuthError(error));
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  const selectVibe = (hint: string) => {
    sessionVibe.day = today;
    sessionVibe.hint = hint;
    setVibeHint(hint);
    setVibeAnswered(true);
  };

  const skipVibe = () => {
    sessionVibe.day = today;
    sessionVibe.hint = null;
    setVibeAnswered(true);
  };

  const closeSwipeDeck = () => {
    setSwipeVisible(false);
    swipeStatus.refetch();
  };

  // ── Render ───────────────────────────────────────────────────────────────

  return (
    <View testID="today-screen" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={{ paddingTop: insets.top + 10, paddingHorizontal: 24, paddingBottom: 120 }}
        refreshControl={
          <RefreshControl refreshing={daily.isRefetching} onRefresh={daily.forceRefresh} tintColor={t.colors.accent} />
        }>
        {/* Header */}
        <View style={{ flexDirection: 'row', alignItems: 'flex-start', marginBottom: 16 }}>
          <View style={{ flex: 1, gap: 5 }}>
            <MonoLabel>{dateLine()}</MonoLabel>
            <View>
              <Text style={[display(32), { color: t.colors.text }]}>{`${greeting()},`}</Text>
              <Text style={[display(32, { italic: true }), { color: t.colors.accent }]}>
                {`${firstName(user?.full_name)}.`}
              </Text>
            </View>
          </View>
          <View
            accessibilityElementsHidden
            importantForAccessibility="no-hide-descendants"
            style={{
              width: 34,
              height: 34,
              borderRadius: 999,
              borderWidth: 1,
              borderColor: t.colors.border,
              alignItems: 'center',
              justifyContent: 'center',
              marginTop: 22,
            }}>
            <AttreqIcon name="menu" size={15} color={t.colors.t2} />
          </View>
        </View>

        <View style={{ marginBottom: 18 }}>
          <WeatherStrip city={city} weather={data?.weather} />
        </View>

        {/* Morning vibe prompt */}
        {showVibe && (
          <Card padding={14} style={{ marginBottom: 18 }}>
            <View style={{ gap: 10 }}>
              <MonoLabel size={10}>Today's vibe?</MonoLabel>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                {VIBES.map((v) => (
                  <Chip
                    key={v.hint}
                    label={v.label}
                    testID={`vibe-chip-${v.hint}`}
                    onPress={() => selectVibe(v.hint)}
                  />
                ))}
                <View style={{ flex: 1 }} />
                <Text
                  onPress={skipVibe}
                  accessibilityRole="button"
                  testID="vibe-skip"
                  style={[mono(10), { color: t.colors.t3 }]}>
                  Skip
                </Text>
              </View>
            </View>
          </Card>
        )}

        {/* State content */}
        {daily.isLoading ? (
          <View style={{ paddingTop: 48, alignItems: 'center' }}>
            <ActivityIndicator color={t.colors.t2} />
          </View>
        ) : isFailed ? (
          <View style={{ gap: 14 }}>
            <View
              style={{
                backgroundColor: t.colors.claySoft,
                borderRadius: 12,
                paddingVertical: 10,
                paddingHorizontal: 13,
              }}>
              <BodyText size={13} color={t.colors.clay}>
                {describeAuthError(daily.error)}
              </BodyText>
            </View>
            <PrimaryButton label="Try again" onPress={() => daily.refetch()} />
          </View>
        ) : isEmpty ? (
          <Card padding={16}>
            <View style={{ gap: 10 }}>
              <MonoLabel size={11}>No looks yet</MonoLabel>
              <BodyText size={13}>
                Your closet is waiting. Add a top and a bottom in the Wardrobe tab and ATTREQ will weave your first
                looks from weather and style.
              </BodyText>
            </View>
          </Card>
        ) : (
          <>
            {/* "Today's looks" heading */}
            <View style={{ flexDirection: 'row', alignItems: 'center', marginBottom: 13 }}>
              <Text style={[display(20, { italic: true }), { color: t.colors.text }]}>Today's looks</Text>
              <View style={{ flex: 1 }} />
              <MonoLabel>{`${suggestions.length} ${suggestions.length === 1 ? 'look' : 'looks'}`}</MonoLabel>
            </View>

            {errorMessage && (
              <View
                style={{
                  backgroundColor: t.colors.claySoft,
                  borderRadius: 12,
                  paddingVertical: 10,
                  paddingHorizontal: 13,
                  marginBottom: 12,
                }}>
                <BodyText size={13} color={t.colors.clay}>
                  {errorMessage}
                </BodyText>
              </View>
            )}

            {current && (
              <RecommendationCard
                suggestion={current}
                lookNumber={currentIndex + 1}
                title={lookTitle(current.occasion_context, currentIndex)}
                isWearing={isWearing}
                isSubmittingFeedback={isSubmittingFeedback}
                onWear={onWear}
                onSkip={onSkip}
                onLove={onLove}
                onDismiss={onDismiss}
              />
            )}

            {/* Pull-down hint */}
            <View style={{ marginTop: 11 }}>
              <Card padding={0}>
                <Text
                  style={[
                    mono(9.5),
                    {
                      color: t.colors.t3,
                      letterSpacing: 1.1,
                      textTransform: 'uppercase',
                      lineHeight: 9.5 * 1.6,
                      paddingVertical: 11,
                      paddingHorizontal: 15,
                    },
                  ]}>
                  Pull down to weave new looks from weather, wardrobe and feedback.
                </Text>
              </Card>
            </View>

            {/* Swipe-deck entry */}
            {showSwipeEntry && (
              <View style={{ marginTop: 11 }}>
                <Card padding={0}>
                  <Pressable
                    accessibilityRole="button"
                    testID="swipe-deck-entry"
                    onPress={() => setSwipeVisible(true)}
                    style={{
                      flexDirection: 'row',
                      alignItems: 'center',
                      paddingVertical: 13,
                      paddingHorizontal: 15,
                    }}>
                    <View style={{ flex: 1, gap: 3 }}>
                      <MonoLabel size={10}>A minute to spare?</MonoLabel>
                      <Text style={[body(14, 'medium'), { color: t.colors.text }]}>Rate a few looks</Text>
                    </View>
                    <AttreqIcon name="chevron" size={14} color={t.colors.t3} />
                  </Pressable>
                </Card>
              </View>
            )}
          </>
        )}
      </ScrollView>

      <RejectionReasonSheet visible={rejectionVisible} onSubmit={onRejectionSubmit} />
      <SwipeDeckModal visible={swipeVisible} onClose={closeSwipeDeck} />
    </View>
  );
}
