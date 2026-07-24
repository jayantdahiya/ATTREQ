import React from 'react';
import Svg, { Circle, Line, Path, Rect } from 'react-native-svg';

// Feather-style 1.5px stroke set — exact paths from assets/design/ios-redesign-v2/attreq-shared.jsx.
export type AttreqIconName =
  | 'sun'
  | 'shirt'
  | 'book'
  | 'person'
  | 'camera'
  | 'image'
  | 'location'
  | 'search'
  | 'bell'
  | 'chevron'
  | 'sparkles'
  | 'back'
  | 'check'
  | 'heart'
  | 'menu'
  | 'x';

export const ATTREQ_ICON_NAMES: AttreqIconName[] = [
  'sun', 'shirt', 'book', 'person', 'camera', 'image', 'location', 'search',
  'bell', 'chevron', 'sparkles', 'back', 'check', 'heart', 'menu', 'x',
];

interface IconProps {
  name: AttreqIconName;
  size?: number;
  color?: string;
  strokeWidth?: number;
}

export function AttreqIcon({ name, size = 20, color = '#A8A29E', strokeWidth }: IconProps) {
  const common = {
    width: size,
    height: size,
    viewBox: '0 0 24 24',
    fill: 'none',
    stroke: color,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
  };
  switch (name) {
    case 'sun':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Circle cx="12" cy="12" r="4" />
          <Line x1="12" y1="2" x2="12" y2="5" />
          <Line x1="12" y1="19" x2="12" y2="22" />
          <Line x1="2" y1="12" x2="5" y2="12" />
          <Line x1="19" y1="12" x2="22" y2="12" />
          <Line x1="4.22" y1="4.22" x2="6.34" y2="6.34" />
          <Line x1="17.66" y1="17.66" x2="19.78" y2="19.78" />
          <Line x1="4.22" y1="19.78" x2="6.34" y2="17.66" />
          <Line x1="17.66" y1="6.34" x2="19.78" y2="4.22" />
        </Svg>
      );
    case 'shirt':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M20.38 3.46 16 2a4 4 0 0 1-8 0L3.62 3.46a2 2 0 0 0-1.34 2.23l.58 3.57a1 1 0 0 0 .99.84H6v10c0 1.1.9 2 2 2h8a2 2 0 0 0 2-2V10h2.15a1 1 0 0 0 .99-.84l.58-3.57a2 2 0 0 0-1.34-2.23z" />
        </Svg>
      );
    case 'book':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
          <Path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </Svg>
      );
    case 'person':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
          <Circle cx="12" cy="7" r="4" />
        </Svg>
      );
    case 'camera':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
          <Circle cx="12" cy="13" r="4" />
        </Svg>
      );
    case 'image':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Rect x="3" y="3" width="18" height="18" rx="2" />
          <Circle cx="8.5" cy="8.5" r="1.5" />
          <Path d="m21 15-5-5L5 21" />
        </Svg>
      );
    case 'location':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
          <Circle cx="12" cy="10" r="3" />
        </Svg>
      );
    case 'search':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Circle cx="11" cy="11" r="8" />
          <Path d="m21 21-4.35-4.35" />
        </Svg>
      );
    case 'bell':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
          <Path d="M13.73 21a2 2 0 0 1-3.46 0" />
        </Svg>
      );
    case 'chevron':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.8}>
          <Path d="m9 18 6-6-6-6" />
        </Svg>
      );
    case 'sparkles':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z" />
        </Svg>
      );
    case 'back':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 2}>
          <Path d="m15 18-6-6 6-6" />
        </Svg>
      );
    case 'check':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 2.2}>
          <Path d="M20 6 9 17l-5-5" />
        </Svg>
      );
    case 'heart':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z" />
        </Svg>
      );
    case 'menu':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.5}>
          <Path d="M4 6h16M4 12h16M4 18h16" />
        </Svg>
      );
    case 'x':
      return (
        <Svg {...common} strokeWidth={strokeWidth ?? 1.8}>
          <Path d="M18 6 6 18M6 6l12 12" />
        </Svg>
      );
    default:
      return null;
  }
}
