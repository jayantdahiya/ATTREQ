import { useEffect, useRef } from 'react';
import { BackHandler, Keyboard } from 'react-native';

// Grace window (ms) after the keyboard hides during which a hardware-back is
// still treated as "just dismiss the keyboard". A single back press both hides
// the keyboard and fires the JS `hardwareBackPress`; those two race, so
// `Keyboard.isVisible()` alone is unreliable (it can already read false by the
// time the handler runs). The window absorbs that race.
const KEYBOARD_DISMISS_GRACE_MS = 350;

/**
 * Registers an Android hardware-back listener for JS-only conditional-render
 * stacks (same register/cleanup idiom as the RN Modal sheets, e.g.
 * SwipeDeckModal). `handler` returns true when it consumed the press (went
 * back one step) and false to fall through to the default behaviour — which
 * exits the app at the root of a stack. Cleans up on unmount. No-op on iOS.
 *
 * When the soft keyboard is open, a back press must only dismiss the keyboard
 * (standard Android behaviour) — it must NOT also pop the step, otherwise a
 * user typing in a field (e.g. the register wizard's city input) gets bounced
 * to the previous step. We swallow the press and dismiss the keyboard when the
 * keyboard is visible OR was visible within the grace window (see above), and
 * only run `handler` once the keyboard is truly down.
 */
export function useBackHandler(handler: () => boolean) {
  // While the keyboard is up this holds Infinity; on hide it holds the deadline
  // until which back-presses are still absorbed as keyboard dismissals.
  const keyboardActiveUntil = useRef(0);

  useEffect(() => {
    const showSub = Keyboard.addListener('keyboardDidShow', () => {
      keyboardActiveUntil.current = Infinity;
    });
    const hideSub = Keyboard.addListener('keyboardDidHide', () => {
      keyboardActiveUntil.current = Date.now() + KEYBOARD_DISMISS_GRACE_MS;
    });
    return () => {
      showSub.remove();
      hideSub.remove();
    };
  }, []);

  useEffect(() => {
    const onHardwareBack = () => {
      if (Keyboard.isVisible() || Date.now() < keyboardActiveUntil.current) {
        Keyboard.dismiss();
        keyboardActiveUntil.current = 0;
        return true;
      }
      return handler();
    };
    const sub = BackHandler.addEventListener('hardwareBackPress', onHardwareBack);
    return () => sub.remove();
  }, [handler]);
}
