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

/** Pick one image from the photo library. Returns null if cancelled. */
export async function pickFromLibrary(): Promise<UploadAsset | null> {
  const result = await launchImageLibrary({ mediaType: 'photo', quality: 0.9, selectionLimit: 1 });
  if (result.didCancel || result.errorCode) return null;
  return toUploadAsset(result.assets?.[0]);
}

/** Capture one image with the camera. Returns null if cancelled. */
export async function pickFromCamera(): Promise<UploadAsset | null> {
  const result = await launchCamera({ mediaType: 'photo', quality: 0.9, saveToPhotos: false });
  if (result.didCancel || result.errorCode) return null;
  return toUploadAsset(result.assets?.[0]);
}
