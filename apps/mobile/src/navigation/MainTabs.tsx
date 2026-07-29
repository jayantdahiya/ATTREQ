import React, { useState } from 'react';
import { View } from 'react-native';
import { useTheme } from '@/design-system/theme/ThemeProvider';
import { TabBar, type AttreqTab } from '@/design-system/components/TabBar';
import { WardrobeStack } from '@/features/wardrobe/WardrobeStack';
import { TodayScreen } from '@/features/today/TodayScreen';
import { HistoryScreen } from '@/features/history/HistoryScreen';
import { ProfilePlaceholderScreen } from '@/features/profile/ProfilePlaceholderScreen';
import { TabPlaceholderScreen } from '@/features/tabs/TabPlaceholderScreen';

/** Authenticated tab shell (JS-only) with the floating pill tab bar. */
export function MainTabs() {
  const t = useTheme();
  const [tab, setTab] = useState<AttreqTab>('today');

  return (
    <View testID="main-tabs" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      {tab === 'today' ? (
        <TodayScreen />
      ) : tab === 'wardrobe' ? (
        <WardrobeStack />
      ) : tab === 'history' ? (
        <HistoryScreen />
      ) : tab === 'profile' ? (
        <ProfilePlaceholderScreen />
      ) : (
        <TabPlaceholderScreen tab={tab} />
      )}
      <TabBar active={tab} onChange={setTab} />
    </View>
  );
}
