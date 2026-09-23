/**
 * **The modal stage** — the one thing an overlay sits on: a full-screen layer above everything,
 * dismissed by the platform's back gesture where there is one, arriving with the overlay's
 * motion. `BottomSheet`, `Popover` and `SearchingLatch` draw on it and nothing else does.
 *
 * Two platforms, one contract, two files. **This file is iOS's** (and the test harness's,
 * which runs as iOS): React Native's `Modal`, a separate native window, which is what a
 * modal always was here. **Android's is `ModalStage.android.tsx`**, a layer in the tree hosted
 * at the root — `overlay.tsx`'s `OverlayHost` says why the native window cannot be used there
 * while Reanimated 3.16 is in the app. Metro picks the file; a caller never chooses.
 *
 * The stage owns nothing an overlay says or does: the scrim, the sheet, the close control are
 * the overlay's, drawn as its children, and a tap on the scrim is the overlay's own decision.
 */

import type { ReactNode } from 'react';
import { Modal } from 'react-native';

export interface ModalStageProps {
  readonly visible: boolean;
  /**
   * The platform asked for the overlay to go — Android's hardware back; iOS never asks. An
   * overlay with no way out answers with nothing and the gesture is swallowed either way.
   */
  readonly onRequestClose: () => void;
  /** How the overlay arrives; `none` under reduced motion, which is the overlay's own call. */
  readonly animationType: 'slide' | 'fade' | 'none';
  /**
   * Where the overlay sits in design-system 9.3's layer order — a sheet under a toast, a
   * popover over one. A native window is above everything whatever it says; the layer in the
   * tree is ordered by it, beside the toast host.
   */
  readonly layer: 'sheet' | 'popover';
  readonly children: ReactNode;
}

export function ModalStage({ visible, onRequestClose, animationType, children }: ModalStageProps) {
  return (
    <Modal
      visible={visible}
      transparent
      onRequestClose={onRequestClose}
      animationType={animationType}
    >
      {children}
    </Modal>
  );
}
