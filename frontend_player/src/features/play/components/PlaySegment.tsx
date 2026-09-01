/**
 * The two ways through the Play tab, as one control: **Find a game** and **Match me**.
 *
 * Design-system [6.3](../../../../docs/design-system.md#63-segmented-control) — *"for a two-
 * or three-way view switch within one screen"*, which is exactly what these are. It is not a
 * chip (a filter over what is on screen) and not a switch (a claim a player makes), and
 * `the-play-components.md` §6.12 draws both of those lines by name.
 *
 * ## The two halves move in opposite directions, and that is the decision here
 *
 * *Find a game* is **an arrival, not a going back.** It calls the shell's own `enterPlay`,
 * which lays `[Now, Find a game]` down and **ends the Play session** on the way — so a player
 * who wandered onto the deck and taps back to the search screen gets the screen the tab opens
 * on, with the week re-seeded, rather than whatever they left behind an hour ago
 * ([#261](https://github.com/Raketa02/Raketa/issues/261)). A `router.back()` here would land
 * in the same place on most paths and in the wrong one on the rest, silently.
 *
 * *Match me* is an ordinary **push**, because the deck genuinely sits on top: Find a game
 * stays underneath it and the platform's own back gesture is then correct without this
 * component owning it.
 *
 * The asymmetry is the shell's rule read out, not a preference: the reset is one function
 * with a growing list of callers, and this is the third.
 *
 * ## The count is the caller's
 *
 * `Match me · 3` is composed by `deckPresentation`, because it is copy and because the number
 * is a read this component has no business making. Both screens that draw this segment already
 * hold it.
 */

import { router } from 'expo-router';

import { enterPlay } from '@/features/shell/types';
import { Segment } from '@/shared/ui';

import { matchMeSegment, matchMeSegmentLabel } from './deckPresentation';
import { FIND_A_GAME_TITLE } from './findAGamePresentation';

/**
 * The deck's route. Play owns its own inner paths — the shell's table holds each tab's
 * **start**, and everything under `/play/…` is this feature's own depth.
 */
export const DECK_ROUTE = '/play/deck';

/** Which of the two the player is looking at. */
export type PlaySurface = 'find' | 'match';

export interface PlaySegmentProps {
  readonly active: PlaySurface;
  /** Your own outstanding yeses in the sport on screen. `0` draws no count. */
  readonly outstanding: number;
}

export function PlaySegment({ active, outstanding }: PlaySegmentProps) {
  return (
    <Segment
      selected={active}
      options={[
        // The screen's own title, rather than a second spelling of it: the segment names a
        // **view**, and the view is that screen. Two constants would be two things to reword.
        { key: 'find', label: FIND_A_GAME_TITLE },
        {
          key: 'match',
          label: matchMeSegment(outstanding),
          accessibilityLabel: matchMeSegmentLabel(outstanding),
        },
      ]}
      onSelect={(surface) => {
        // A press on the half already showing is deliberately not swallowed on `find`: the
        // segment reports every press (`Segment`), and re-entering Play is an act with an
        // effect — it lays the stack down again and clears the session.
        if (surface === 'find') return enterPlay();
        if (active !== 'match') router.push(DECK_ROUTE);
      }}
    />
  );
}
