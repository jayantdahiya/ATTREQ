import { bucketFor, matchesFilter } from '@/features/wardrobe/categories';

describe('wardrobe category bucketing', () => {
  it('buckets free-text categories with the right precedence', () => {
    expect(bucketFor('Blue Jeans')).toBe('bottoms');
    expect(bucketFor('Pleated skirt')).toBe('bottoms');
    expect(bucketFor('White sneakers')).toBe('shoes');
    expect(bucketFor('Leather boots')).toBe('shoes');
    expect(bucketFor('Wool coat')).toBe('outer');
    expect(bucketFor('Denim jacket')).toBe('outer');
    expect(bucketFor('Leather handbag')).toBe('accents');
    expect(bucketFor('Silk scarf')).toBe('accents');
    expect(bucketFor('Linen shirt')).toBe('tops');
    expect(bucketFor('Dress')).toBe('tops'); // deliberately falls through to tops
    expect(bucketFor(null)).toBe('tops');
  });

  it('matchesFilter: all matches everything, specific filters bucket', () => {
    expect(matchesFilter('all', 'Jeans')).toBe(true);
    expect(matchesFilter('bottoms', 'Jeans')).toBe(true);
    expect(matchesFilter('tops', 'Jeans')).toBe(false);
    expect(matchesFilter('shoes', 'Sneakers')).toBe(true);
  });
});
