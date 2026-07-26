import React, { useState } from 'react';
import { WardrobeScreen } from '@/features/wardrobe/WardrobeScreen';
import { WardrobeItemDetailScreen } from '@/features/wardrobe/WardrobeItemDetailScreen';
import { ArchivedWardrobeScreen } from '@/features/wardrobe/ArchivedWardrobeScreen';

type Screen = { name: 'list' } | { name: 'detail'; itemId: string } | { name: 'archived' };

/** JS-only stack for the Wardrobe tab: list ↔ detail ↔ archived. */
export function WardrobeStack() {
  const [screen, setScreen] = useState<Screen>({ name: 'list' });

  if (screen.name === 'detail') {
    return <WardrobeItemDetailScreen itemId={screen.itemId} onBack={() => setScreen({ name: 'list' })} />;
  }
  if (screen.name === 'archived') {
    return (
      <ArchivedWardrobeScreen
        onBack={() => setScreen({ name: 'list' })}
        onOpenItem={(itemId) => setScreen({ name: 'detail', itemId })}
      />
    );
  }
  return (
    <WardrobeScreen
      onOpenItem={(itemId) => setScreen({ name: 'detail', itemId })}
      onOpenArchived={() => setScreen({ name: 'archived' })}
    />
  );
}
