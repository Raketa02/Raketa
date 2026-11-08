/**
 * **The hero's room, measured** — the picture's view takes `onLayout`, and the deck (#786) and the
 * podium (#788) draw nothing until it has answered ([#786](https://github.com/Raketa02/Raketa/issues/786),
 * [#788](https://github.com/Raketa02/Raketa/issues/788); design system 12.2). A short phone, a tall
 * one, and a headline at the text cap's three lines each leave a different room, which is why nothing
 * computes one; a frame drawn at the wrong size before the answer would be a jump.
 */

import { useState } from 'react';
import type { LayoutChangeEvent } from 'react-native';

import type { Size } from './stageFit';

/** The room a picture is drawn in, as its `onLayout` measures it. */
export interface MeasuredRoom {
  readonly room: Size;
  /** Whether it has been laid out yet — nothing is drawn until it has. */
  readonly measured: boolean;
  readonly onLayout: (event: LayoutChangeEvent) => void;
}

const UNMEASURED: Size = { width: 0, height: 0 };

/** The room, measured by the view that takes `onLayout`. */
export function useMeasuredRoom(): MeasuredRoom {
  const [room, setRoom] = useState<Size>(UNMEASURED);

  const onLayout = ({ nativeEvent }: LayoutChangeEvent) =>
    setRoom({ width: nativeEvent.layout.width, height: nativeEvent.layout.height });

  return { room, measured: room.width > 0 && room.height > 0, onLayout };
}
