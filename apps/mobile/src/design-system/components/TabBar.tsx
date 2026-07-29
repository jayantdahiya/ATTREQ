import React from 'react';
import { Pressable, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useTheme } from '../theme/ThemeProvider';
import { mono } from '../theme/typography';
import { tabActiveBg, tabBarSurface } from '../theme/theme';
import { AttreqIcon, AttreqIconName } from '../icons/AttreqIcon';

export type AttreqTab = 'today' | 'wardrobe' | 'history' | 'profile';

const TABS: { key: AttreqTab; label: string; icon: AttreqIconName }[] = [
  { key: 'today', label: 'TODAY', icon: 'sun' },
  { key: 'wardrobe', label: 'WARDROBE', icon: 'shirt' },
  { key: 'history', label: 'HISTORY', icon: 'book' },
  { key: 'profile', label: 'PROFILE', icon: 'person' },
];

// Floating pill tab bar — bottom-inset, semi-opaque surface (Android blur approximation).
export function TabBar({ active, onChange }: { active: AttreqTab; onChange: (tab: AttreqTab) => void }) {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  return (
    <View
      style={{
        position: 'absolute',
        left: 16,
        right: 16,
        bottom: Math.max(insets.bottom, 20),
        backgroundColor: tabBarSurface(t.isDark),
        borderRadius: 22,
        borderWidth: 1,
        borderColor: t.colors.border,
        flexDirection: 'row',
        padding: 4,
        shadowColor: '#000',
        shadowOpacity: t.isDark ? 0.3 : 0.08,
        shadowRadius: 16,
        shadowOffset: { width: 0, height: 8 },
        elevation: 12,
      }}>
      {TABS.map(tab => {
        const on = active === tab.key;
        return (
          <Pressable
            key={tab.key}
            onPress={() => onChange(tab.key)}
            accessibilityRole="tab"
            accessibilityState={{ selected: on }}
            style={{
              flex: 1,
              alignItems: 'center',
              gap: 2,
              paddingVertical: 5,
              borderRadius: 16,
              backgroundColor: on ? tabActiveBg(t.isDark) : 'transparent',
            }}>
            <AttreqIcon name={tab.icon} size={19} color={on ? t.colors.text : t.colors.t3} />
            <Text style={[mono(7), { letterSpacing: 0.7, color: on ? t.colors.text : t.colors.t3 }]}>{tab.label}</Text>
          </Pressable>
        );
      })}
    </View>
  );
}
