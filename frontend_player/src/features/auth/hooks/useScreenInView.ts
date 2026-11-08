/**
 * **Whether this route is the screen in view** — the navigator's focus, as a value
 * ([#784](https://github.com/Raketa02/Raketa/issues/784)).
 *
 * The stage draws a light status bar over its hero, and a stack keeps sign-in mounted under the
 * screen pushed over it, so *mounted* is not *in view*: the bar has to go when *Forgot password?*
 * covers sign-in and come back when it is popped. The sign-in loop (#787) will stop and start on the
 * same value.
 *
 * **Read in the route file and handed to the screen as a prop**, never inside the screen: the
 * navigator's hooks throw outside a navigator, and the auth suites draw the screens on their own,
 * where the screen is — trivially — the one in view. Starts at what the navigator says now, so a
 * screen mounted under another is not drawn as in view for a frame.
 */

import { useFocusEffect, useNavigation } from 'expo-router';
import { useCallback, useState } from 'react';

export function useScreenInView(): boolean {
  const navigation = useNavigation();
  const [inView, setInView] = useState(() => navigation.isFocused());

  useFocusEffect(
    useCallback(() => {
      setInView(true);
      return () => setInView(false);
    }, []),
  );

  return inView;
}
