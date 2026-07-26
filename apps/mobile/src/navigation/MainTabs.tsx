import React, { useState } from 'react';
import { View } from 'react-native';
import { useTheme } from '@/design-system/theme/ThemeProvider';
import { TabBar, type AttreqTab } from '@/design-system/components/TabBar';
import { WardrobeStack } from '@/features/wardrobe/WardrobeStack';
import { ProfilePlaceholderScreen } from '@/features/profile/ProfilePlaceholderScreen';
import { TabPlaceholderScreen } from '@/features/tabs/TabPlaceholderScreen';

/** Authenticated tab shell (JS-only) with the floating pill tab bar. */
export function MainTabs() {
  const t = useTheme();
  // Default to Wardrobe (the milestone built through A2); Today lands in A4.
  const [tab, setTab] = useState<AttreqTab>('wardrobe');

  return (
    <View testID="main-tabs" style={{ flex: 1, backgroundColor: t.colors.bg }}>
      {tab === 'wardrobe' ? (
        <WardrobeStack />
      ) : tab === 'profile' ? (
        <ProfilePlaceholderScreen />
      ) : (
        <TabPlaceholderScreen tab={tab} />
      )}
      <TabBar active={tab} onChange={setTab} />
    </View>
  );
}
