import { useEffect } from 'react';
import { BackHandler } from 'react-native';

/**
 * Registers an Android hardware-back listener for JS-only conditional-render
 * stacks (same register/cleanup idiom as the RN Modal sheets, e.g.
 * SwipeDeckModal). `handler` returns true when it consumed the press (went
 * back one step) and false to fall through to the default behaviour — which
 * exits the app at the root of a stack. Cleans up on unmount. No-op on iOS.
 */
export function useBackHandler(handler: () => boolean) {
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', handler);
    return () => sub.remove();
  }, [handler]);
}
