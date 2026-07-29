import {
  detectedItemDetail,
  detectedItemTitle,
  detectedItemsPreview,
  extractDetectedItems,
} from '@/features/onboarding/detected-items';
import type { StyleDnaPhoto, StyleDnaUploadResponse } from '@/lib/api/types';

function photo(extraction: Record<string, unknown> | null): StyleDnaPhoto {
  return {
    id: 'p',
    user_id: 'u',
    file_path: 'x',
    file_url: '/x',
    quality_ok: true,
    quality_reason: null,
    per_photo_extraction: extraction,
    created_at: '2026-01-01T00:00:00Z',
  };
}

function response(photos: StyleDnaPhoto[]): StyleDnaUploadResponse {
  return { photos_processed: photos.length, photos_skipped: 0, wardrobe_items_seeded: 0, style_dna: null, photos };
}

describe('extractDetectedItems', () => {
  it('flattens items across photos and tolerates snake_case + camelCase keys', () => {
    const items = extractDetectedItems(
      response([
        photo({
          wardrobe_items_detected: [
            {
              category: 'top',
              subcategory: 'oxford shirt',
              color_primary: 'white',
              color_secondary: null,
              pattern: 'solid',
              occasion: ['work'],
              season: ['all'],
              confidence: 0.91,
              bounding_region: 'upper body',
            },
          ],
        }),
        photo({
          // camelCase container + item keys still resolve.
          wardrobeItemsDetected: [
            { category: 'bottom', subcategory: 'chinos', colorPrimary: 'navy', confidence: 0.84 },
          ],
        }),
      ]),
    );

    expect(items).toHaveLength(2);
    expect(items[0]).toMatchObject({
      category: 'top',
      subcategory: 'oxford shirt',
      colorPrimary: 'white',
      colorSecondary: null,
      pattern: 'solid',
      occasion: ['work'],
      season: ['all'],
      confidence: 0.91,
      boundingRegion: 'upper body',
    });
    expect(items[1]).toMatchObject({ category: 'bottom', subcategory: 'chinos', colorPrimary: 'navy', confidence: 0.84 });
    // Defaults applied for missing optional fields.
    expect(items[1].occasion).toEqual([]);
    expect(items[1].boundingRegion).toBe('');
  });

  it('skips photos without extraction, without the array, and items without a category', () => {
    const items = extractDetectedItems(
      response([
        photo(null),
        photo({ something_else: true }),
        photo({ wardrobe_items_detected: [{ subcategory: 'no category here' }, 'garbage', null] }),
      ]),
    );
    expect(items).toEqual([]);
  });

  it('derives display title, detail line, and preview', () => {
    const items = extractDetectedItems(
      response([
        photo({
          wardrobe_items_detected: [
            { category: 'top', subcategory: 'blazer', color_primary: 'camel', color_secondary: 'brown', pattern: 'solid', confidence: 0.7 },
            { category: 'shoes', subcategory: '', color_primary: 'black', confidence: 0.6 },
            { category: 'bottom', subcategory: 'jeans', color_primary: 'blue', confidence: 0.5 },
            { category: 'accessory', subcategory: 'belt', color_primary: 'tan', confidence: 0.4 },
          ],
        }),
      ]),
    );

    expect(detectedItemTitle(items[0])).toBe('Blazer');
    expect(detectedItemTitle(items[1])).toBe('Shoes'); // empty subcategory → category
    expect(detectedItemDetail(items[0])).toBe('camel / brown · solid');
    expect(detectedItemsPreview(items)).toBe('camel blazer · black shoes · blue jeans · +1 more');
  });
});
