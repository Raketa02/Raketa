/**
 * `mmsearch` — **where the wait happens**, and a latch over the screen that launched it
 * ([#269](https://github.com/Raketa02/Raketa/issues/269)).
 *
 * ## It is bound to the response, and that is what dissolved the dead end
 *
 * The prototype ran this on a 1400 ms timer and gave it *no back button and no escape*, which
 * made it a place a player could be stranded with nothing to retry. Binding it to the request
 * instead removes the dead end rather than furnishing it: the latch is up because something is
 * in flight, it holds the answer for a beat once one exists, and a refusal takes it down at
 * once over the control that failed — the screen's own *Search*, because nothing was minted
 * (`domain/retryTarget`).
 *
 * **The beat after the answer is the count's, and is why the count is worth having.** The
 * floor runs from the response rather than from the press, so a search that took five seconds
 * prints its number for exactly as long as one that took fifty milliseconds; anchored the
 * other way it would print for whatever was left of the floor, which on a real round trip is
 * nothing (`heldWait`).
 *
 * So there is **no control here of any kind**. A close would promise an escape from a wait the
 * player is not trapped in, and a back would make this a destination. What keeps a fast answer
 * from flashing past is the floor, not a button (`heldWait`).
 *
 * ## The count is printed off the answer or not at all
 *
 * §B14's *live* count was `len(generation.admitted)` on a timer, printed **before the response
 * existed**. It is now `players_in_range` from the response, and the shape says so:
 * `SearchingStatus.count` is absent until there is one, so the wait states what it is doing
 * and prints no number it could not have.
 *
 * That is also the whole of §20.11's *"the searching region announces the **result** once and
 * never a stage"*: the count is the result, it appears once, and `useLiveRegion` says
 * something only when it changes.
 *
 * ## A `Modal`, for the same three reasons the sheet is one
 *
 * Siblings hidden natively, `accessibilityViewIsModal` inside, and — the one that matters here
 * — **Android's hardware back arrives at `onRequestClose` and is answered with nothing**. That
 * is *no escape* stated to the platform rather than left to the absence of a control. The
 * screen behind still spreads `behindOverlay` itself, which is the half a `Modal` cannot do
 * for it.
 *
 * The transition is skipped under reduced motion, which is `BottomSheet`'s own choice for the
 * same question and read from the same context — one subscription for the tree rather than one
 * per surface, on a component that is mounted for as long as the screen is. §20.11's *second
 * condition on the same path* governs the **craft**: the fill's staggered seats and the deck's
 * card, where a listener would be made to wait through presentation over an answer already in
 * memory. A cross-fade on an overlay is not that, and the sheet settled it first.
 *
 * The **hold** underneath is skipped by neither, and the difference is `motion.hold`'s:
 * nothing moves during a hold, so there is no animation to spare anybody.
 *
 * **Focus is not moved, and that is the one overlay obligation this surface answers
 * differently.** The sheet moves focus in because it is a place to do something and back out
 * because the player chose to leave; this has nothing to focus and nobody chose to leave it.
 * What Part 13 actually asks of something that appears unasked is that it **announces**, and
 * §20.11 fixes what it announces and when: the result, once, and never a stage. Moving focus
 * onto a headline and off it again inside one second would be two interruptions in place of
 * the one sentence that carries the answer.
 */

import { ActivityIndicator, Modal, StyleSheet, Text, View } from 'react-native';

import { theme, useLiveRegion, useReducedMotion } from '@/shared/ui';

import { PLAY_LIVE_REGIONS } from './accessibilityPresentation';
import type { SearchingStatus } from './searchingPresentation';

export interface SearchingLatchProps {
  /** Whether the wait is up. Owned by the screen, which holds the request and the floor. */
  readonly visible: boolean;
  /** The headline, and the count once the response has one. */
  readonly status: SearchingStatus;
}

export function SearchingLatch({ visible, status }: SearchingLatchProps) {
  const reducedMotion = useReducedMotion();

  // The result, once. A stage has nothing to announce and `null` is a region with nothing in
  // it, which is silence rather than an empty sentence.
  useLiveRegion(visible ? (status.count ?? null) : null, PLAY_LIVE_REGIONS.searching);

  return (
    <Modal
      visible={visible}
      // Android's hardware back, answered with nothing: a latch is not a destination, so
      // there is nowhere for it to go back to.
      onRequestClose={NO_ESCAPE}
      animationType={reducedMotion ? 'none' : 'fade'}
    >
      <View style={s.stage} accessibilityViewIsModal>
        {/* Unlabelled: the headline below is the accessible announcement, and an indicator
            naming the same thing would say it twice (`CalculatingScreen`). */}
        <ActivityIndicator size="large" color={theme.color.coral} accessibilityElementsHidden />

        <Text style={s.headline} accessibilityRole="header">
          {status.headline}
        </Text>

        {status.count === undefined ? null : <Text style={s.count}>{status.count}</Text>}
      </View>
    </Modal>
  );
}

/** Named rather than inlined, so the empty body reads as the decision it is. */
const NO_ESCAPE = () => undefined;

const s = StyleSheet.create({
  stage: {
    flex: 1,
    backgroundColor: theme.color.paper,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: theme.size.gutter,
    gap: theme.space.lg,
  },
  headline: { ...theme.type.h1, color: theme.color.ink, textAlign: 'center' },
  count: { ...theme.type.tiny, color: theme.color.muted, textAlign: 'center' },
});
