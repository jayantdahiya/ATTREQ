// Free-text color name → display hex, for Style DNA palette swatches. Ported
// from iOS StyleDnaProfileView.SwatchPalette. Longest matching key wins
// ("light blue" beats "blue"); unknown names fall back to a neutral stone so a
// swatch never renders invisibly.

const FALLBACK = '#A19A91';

// Ordered longest-first within each family so `.find(contains)` matches the
// most specific name available.
const TABLE: [string, string][] = [
  ['off-white', '#F5F2EA'],
  ['off white', '#F5F2EA'],
  ['light blue', '#A3C2DC'],
  ['sky blue', '#A3C2DC'],
  ['charcoal', '#3A3733'],
  ['espresso', '#4A362A'],
  ['chocolate', '#5A4232'],
  ['turquoise', '#53B0AE'],
  ['terracotta', '#C2664A'],
  ['burgundy', '#6E2B33'],
  ['lavender', '#A99BC6'],
  ['emerald', '#2E7D5B'],
  ['mustard', '#C99A34'],
  ['apricot', '#E8A96B'],
  ['crimson', '#A5273B'],
  ['fuchsia', '#B0368C'],
  ['magenta', '#B0368C'],
  ['oatmeal', '#E4DCC9'],
  ['caramel', '#B07B4F'],
  ['coffee', '#6B4F3B'],
  ['forest', '#3C5941'],
  ['cobalt', '#2E5AA8'],
  ['indigo', '#3F4470'],
  ['maroon', '#6B2B36'],
  ['salmon', '#E8927C'],
  ['silver', '#B9B6B0'],
  ['ivory', '#F6F0E1'],
  ['cream', '#F1E8D8'],
  ['stone', '#C9C2B6'],
  ['beige', '#D9C9AF'],
  ['camel', '#B98F62'],
  ['khaki', '#A79A6E'],
  ['taupe', '#A99C8F'],
  ['brown', '#7A5C43'],
  ['olive', '#6E6F45'],
  ['green', '#567A5B'],
  ['denim', '#5D7A9B'],
  ['navy', '#27364D'],
  ['plum', '#6E4560'],
  ['mauve', '#A8848E'],
  ['coral', '#E0796A'],
  ['peach', '#EFC4A6'],
  ['blush', '#E7B9B4'],
  ['black', '#1C1917'],
  ['white', '#FAF8F5'],
  ['ecru', '#EADFC8'],
  ['sand', '#D9C39A'],
  ['sage', '#A3B29A'],
  ['mint', '#A9D3B5'],
  ['teal', '#3D7A78'],
  ['blue', '#4A6FA5'],
  ['lilac', '#C1AED4'],
  ['purple', '#6F5A93'],
  ['wine', '#703043'],
  ['rust', '#A65432'],
  ['gold', '#C4A24E'],
  ['pink', '#D998A7'],
  ['rose', '#C97A85'],
  ['grey', '#8A857E'],
  ['gray', '#8A857E'],
  ['tan', '#C8A97D'],
  ['red', '#B03A2E'],
  ['yellow', '#E4C24E'],
  ['orange', '#D08434'],
];

export function swatchColor(name: string): string {
  const key = name.toLowerCase().trim();
  const exact = TABLE.find(([k]) => k === key);
  if (exact) return exact[1];
  let best: [string, string] | undefined;
  for (const entry of TABLE) {
    if (key.includes(entry[0]) && (!best || entry[0].length > best[0].length)) {
      best = entry;
    }
  }
  return best?.[1] ?? FALLBACK;
}
