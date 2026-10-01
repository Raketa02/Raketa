/**
 * **A screen's frame, its top edge clear of the status bar** — the top safe-area inset as padding,
 * read from the provider, where a screen used to wear `react-native-safe-area-context`'s
 * `SafeAreaView edges={['top']}`.
 *
 * **The native view measures itself after it is drawn.** Under the new architecture its first
 * frame has no inset — the header sits under the status bar — and the next frame moves the whole
 * screen down by it. A screen that slides in hides that inside the motion; a tab root arrives with
 * none (the shells' `animation: 'none'`), so the jump *is* the tab press, and on Android it read
 * as the header blinking between the two screens (#529). The provider has known the insets since
 * the app's first frame (`initialMetrics`, the root layout), so padding from it is right first time.
 *
 * **The top edge only**, for 10.1's reason: the bottom inset is the tab bar's. The inset wins over
 * a `paddingTop` in `style`, because a screen that padded its own top would be under the status
 * bar again.
 */

import type { ReactNode } from 'react';
import { View, type StyleProp, type ViewStyle } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

export interface TopSafeAreaProps {
  readonly style?: StyleProp<ViewStyle>;
  readonly children: ReactNode;
}

export function TopSafeArea({ style, children }: TopSafeAreaProps) {
  const { top } = useSafeAreaInsets();

  return <View style={[style, { paddingTop: top }]}>{children}</View>;
}
