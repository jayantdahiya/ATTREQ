import { useCallback, useState } from 'react';

import { styleDnaApi } from '@/lib/api/style-dna';
import { wardrobeApi, type UploadAsset } from '@/lib/api/wardrobe';
import { usersApi } from '@/lib/api/users';
import { queryClient, queryKeys } from '@/lib/query/query-client';
import { describeAuthError } from '@/lib/api/errors';
import { extractDetectedItems } from '@/features/onboarding/detected-items';
import type { DetectedWardrobeItem, StyleDnaUploadResponse } from '@/lib/api/types';

export const MIN_PHOTOS = 3;
export const MAX_PHOTOS = 8;
export const MAX_CAPTURE_PHOTOS = 20;
export const RECOMMENDED_ITEM_TARGET = 10;

export type UploadState = 'idle' | 'uploading' | 'failed';
export type CaptureState = 'idle' | 'uploading' | 'done' | 'failed';
export type PersonalColorState = 'idle' | 'analyzing' | 'done' | 'failed';

/**
 * Onboarding state machine — the RN analogue of iOS OnboardingViewModel. Holds
 * the Style DNA outfit photos, the upload result + detected items, the review
 * selection, the batch wardrobe-capture photos, and the optional selfie step,
 * plus the shared `complete()` that flips `onboarding_completed` so the root
 * gate advances to the tabs.
 */
export function useOnboardingController() {
  // Step 1 — Style DNA outfit photos.
  const [photos, setPhotos] = useState<UploadAsset[]>([]);
  const [uploadState, setUploadState] = useState<UploadState>('idle');
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadResponse, setUploadResponse] = useState<StyleDnaUploadResponse | null>(null);

  // Detected items + advisory review selection.
  const [detectedItems, setDetectedItems] = useState<DetectedWardrobeItem[]>([]);
  const [reviewSelection, setReviewSelection] = useState<Set<number>>(new Set());

  // Step 4 — batch wardrobe capture.
  const [capturePhotos, setCapturePhotos] = useState<UploadAsset[]>([]);
  const [captureState, setCaptureState] = useState<CaptureState>('idle');
  const [captureError, setCaptureError] = useState<string | null>(null);
  const [wardrobeItemCount, setWardrobeItemCount] = useState(0);

  // Step 5 — optional personal-color selfie.
  const [personalColorState, setPersonalColorState] = useState<PersonalColorState>('idle');
  const [personalColorError, setPersonalColorError] = useState<string | null>(null);

  // Completion.
  const [isCompleting, setIsCompleting] = useState(false);
  const [completionError, setCompletionError] = useState<string | null>(null);

  const isUploading = uploadState === 'uploading';
  const canBuild = photos.length >= MIN_PHOTOS;

  const addPhotos = useCallback((newPhotos: UploadAsset[]) => {
    setPhotos((prev) => {
      const remaining = MAX_PHOTOS - prev.length;
      if (remaining <= 0) return prev;
      return [...prev, ...newPhotos.slice(0, remaining)];
    });
  }, []);

  const removePhoto = useCallback((index: number) => {
    setPhotos((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // POST /users/style-dna/upload. Any retry (after failed) or rebuild first
  // best-effort deletes the stored seed set so re-uploads REPLACE rather than
  // accumulate (the upload endpoint always appends).
  const build = useCallback(async (): Promise<boolean> => {
    if (!canBuild || uploadState === 'uploading') return false;
    const isFirstAttempt = uploadState === 'idle';
    setUploadState('uploading');
    setUploadError(null);
    if (!isFirstAttempt) {
      try {
        await styleDnaApi.deleteStylePhotos();
      } catch {
        // Best-effort — proceed with upload regardless.
      }
    }
    try {
      const response = await styleDnaApi.uploadStylePhotos(photos);
      const items = extractDetectedItems(response);
      setUploadResponse(response);
      setDetectedItems(items);
      setReviewSelection(new Set(items.map((_, i) => i)));
      setUploadState('idle');
      // Upload seeds the wardrobe server-side; keep our counter fresh.
      void refreshWardrobeCount();
      return true;
    } catch (e) {
      setUploadError(describeAuthError(e));
      setUploadState('failed');
      return false;
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [canBuild, photos, uploadState]);

  const toggleReviewItem = useCallback((index: number) => {
    setReviewSelection((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }, []);

  const addCapturePhotos = useCallback((newPhotos: UploadAsset[]) => {
    setCapturePhotos((prev) => {
      const remaining = MAX_CAPTURE_PHOTOS - prev.length;
      if (remaining <= 0) return prev;
      return [...prev, ...newPhotos.slice(0, remaining)];
    });
  }, []);

  const removeCapturePhoto = useCallback((index: number) => {
    setCapturePhotos((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const refreshWardrobeCount = useCallback(async () => {
    try {
      const response = await wardrobeApi.list('active', 1);
      setWardrobeItemCount(response.total);
    } catch {
      // Silent — keep the last known count.
    }
  }, []);

  // POST /wardrobe/batch-upload for every captured/picked garment photo.
  const uploadCapturePhotos = useCallback(async () => {
    if (capturePhotos.length === 0 || captureState === 'uploading') return;
    setCaptureState('uploading');
    setCaptureError(null);
    try {
      await wardrobeApi.batchUpload(capturePhotos);
      setCapturePhotos([]);
      setCaptureState('done');
      await refreshWardrobeCount();
    } catch (e) {
      setCaptureError(describeAuthError(e));
      setCaptureState('failed');
    }
  }, [capturePhotos, captureState, refreshWardrobeCount]);

  // POST /users/style-dna/selfie — soft-fail always. 404 (feature off), 400
  // (consent), or any error all degrade to "no estimate this time"; the flow
  // always keeps a forward path.
  const estimatePersonalColor = useCallback(
    async (asset: UploadAsset, consent: boolean) => {
      if (personalColorState === 'analyzing') return;
      setPersonalColorState('analyzing');
      setPersonalColorError(null);
      try {
        await styleDnaApi.estimatePersonalColorSelfie(asset, consent);
        setPersonalColorState('done');
      } catch (e) {
        setPersonalColorError(describeAuthError(e));
        setPersonalColorState('failed');
      }
    },
    [personalColorState],
  );

  // POST /users/onboarding/complete → flips onboarding_completed; writing the
  // refreshed user into the `me` cache advances the root gate to the tabs
  // (same pattern as the A1 OnboardingPlaceholderScreen).
  const complete = useCallback(async () => {
    if (isCompleting) return;
    setIsCompleting(true);
    setCompletionError(null);
    try {
      const user = await usersApi.completeOnboarding();
      queryClient.setQueryData(queryKeys.me, user);
    } catch (e) {
      setCompletionError(describeAuthError(e));
    } finally {
      setIsCompleting(false);
    }
  }, [isCompleting]);

  return {
    // Step 1
    photos,
    uploadState,
    uploadError,
    uploadResponse,
    isUploading,
    canBuild,
    addPhotos,
    removePhoto,
    build,
    // Review
    detectedItems,
    reviewSelection,
    toggleReviewItem,
    // Step 4
    capturePhotos,
    captureState,
    captureError,
    wardrobeItemCount,
    itemsRemaining: Math.max(0, RECOMMENDED_ITEM_TARGET - wardrobeItemCount),
    addCapturePhotos,
    removeCapturePhoto,
    refreshWardrobeCount,
    uploadCapturePhotos,
    // Step 5
    personalColorState,
    personalColorError,
    estimatePersonalColor,
    // Completion
    isCompleting,
    completionError,
    complete,
  };
}

export type OnboardingController = ReturnType<typeof useOnboardingController>;
