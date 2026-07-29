import { PermissionsAndroid, Platform } from 'react-native';
import { launchCamera, launchImageLibrary, type Asset } from 'react-native-image-picker';
import type { UploadAsset } from '@/lib/api/wardrobe';

function toUploadAsset(asset: Asset | undefined): UploadAsset | null {
  if (!asset?.uri) return null;
  return {
    uri: asset.uri,
    name: asset.fileName ?? `wardrobe-${Date.now()}.jpg`,
    type: asset.type ?? 'image/jpeg',
  };
}

/**
 * The manifest declares android.permission.CAMERA, which makes the runtime
 * grant mandatory before launchCamera can open the camera (it otherwise fails
 * with errorCode 'others'). Requests at point of use; throws a user-showable
 * Error when denied. No-op on iOS (launchCamera drives the iOS prompt).
 */
async function ensureCameraPermission(): Promise<void> {
  if (Platform.OS !== 'android') return;
  const alreadyGranted = await PermissionsAndroid.check(PermissionsAndroid.PERMISSIONS.CAMERA);
  if (alreadyGranted) return;
  const status = await PermissionsAndroid.request(PermissionsAndroid.PERMISSIONS.CAMERA, {
    title: 'Camera access',
    message: 'ATTREQ uses your camera to photograph your clothes.',
    buttonPositive: 'OK',
    buttonNegative: 'Cancel',
  });
  if (status === PermissionsAndroid.RESULTS.GRANTED) return;
  if (status === PermissionsAndroid.RESULTS.NEVER_ASK_AGAIN) {
    throw new Error('Camera access is turned off. Enable Camera for ATTREQ in your device Settings.');
  }
  throw new Error('Camera access is needed to take photos.');
}

/** Pick one image from the photo library. Returns null if cancelled. */
export async function pickFromLibrary(): Promise<UploadAsset | null> {
  const result = await launchImageLibrary({ mediaType: 'photo', quality: 0.9, selectionLimit: 1 });
  if (result.didCancel || result.errorCode) return null;
  return toUploadAsset(result.assets?.[0]);
}

/**
 * Capture one image with the camera. Returns null if cancelled; throws an
 * Error with a user-showable message when permission is denied or the picker
 * reports an errorCode.
 */
export async function pickFromCamera(): Promise<UploadAsset | null> {
  await ensureCameraPermission();
  const result = await launchCamera({ mediaType: 'photo', quality: 0.9, saveToPhotos: false });
  if (result.didCancel) return null;
  if (result.errorCode) {
    throw new Error(
      result.errorCode === 'camera_unavailable'
        ? 'No camera is available on this device.'
        : result.errorMessage || `Could not open the camera (${result.errorCode}).`,
    );
  }
  return toUploadAsset(result.assets?.[0]);
}

/**
 * Multi-select from the photo library, capped at `max`. Returns [] if
 * cancelled. Used by Style DNA upload (3–8 outfits) and batch wardrobe capture
 * (up to 20 garments). `selectionLimit: 0` means unlimited in
 * react-native-image-picker, so clamp to at least 1.
 */
export async function pickMultipleFromLibrary(max: number): Promise<UploadAsset[]> {
  const result = await launchImageLibrary({
    mediaType: 'photo',
    quality: 0.9,
    selectionLimit: Math.max(1, max),
  });
  if (result.didCancel || result.errorCode) return [];
  return (result.assets ?? [])
    .map(toUploadAsset)
    .filter((a): a is UploadAsset => a !== null);
}
