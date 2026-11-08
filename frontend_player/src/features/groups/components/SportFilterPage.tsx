/**
 * **A page filtered by the fast filter** — the group page and Members
 * ([#513](https://github.com/Raketa02/Raketa/issues/513),
 * [#514](https://github.com/Raketa02/Raketa/issues/514)): its header with the sport pill, what is
 * under the header for the sport chosen, and the bar the pill unfolds into, floating over both.
 *
 * **The pill, the bar and the layer they open on are shared UI's** — `SportPillFrame`, the one
 * control Rankings draws too ([#774](https://github.com/Raketa02/Raketa/issues/774)). What is the
 * group page's is here: the filter's state, and its words.
 *
 * **One filter, one state**: the sport is `useGroupSport`'s, the one value last picked anywhere in
 * Play, so a sport picked on Members is the sport the group page is on when the player goes back,
 * and the other way round (story 58).
 *
 * **The open bar covers the group's tile whole or not at all** (#529). The header hands the tile
 * to `cover`, and the bar opens over it with `space.xs` to spare — which stops short of the back
 * arrow, a `space.sm` gap before the tile. Members has no tile, and covers nothing.
 *
 * The page draws its own header and body, handed what they need: the header the pill, once there
 * is a sport to show, and the sport itself — Members counts its list in its title — and the body
 * the sport — `undefined` until the phone has answered, so
 * nothing is drawn for one sport and then another (ADR-0188 §4) — and, for an official group the
 * reader is rated in none of the sports of, what they would add to see it (#519); for a player
 * group's reader rated in nothing, that they meet the door where play begins (#730).
 *
 * **The bar ends with *+ Another sport*** while there is a sport left to offer (#731, ADR-0200 §4):
 * pressed, it folds and hands the page the sports it offers (`onAnother`), and the page opens the
 * picker for a pass that returns to it — the tab is the page's to say. A page that hands no
 * `onAnother` offers none.
 *
 * **The filter's state can be handed in** (`SportFilterFrame`): the Administrator's Members lists
 * an official group's declared sports whatever the reader is rated in (#529), so it brings its own
 * state and draws the same header, pill and bar.
 */

import type { ReactNode } from 'react';

import { PICKER_HINT, sportLabel } from '@/features/onboarding/types';
import { SportPillFrame, type AnotherSport, type SportPillWords } from '@/shared/ui';
import type { Sport } from '@/shared/vocabulary/sport';

import { useGroupSport, type GroupSport } from '../hooks/useGroupSport';

import { GROUPS_COPY } from './groupsCopy';
import { sportPillLabel } from './groupsPresentation';

const COPY = GROUPS_COPY.filter;

/**
 * The fast filter's words. The two names are read at the call, never at load: the feature barrels
 * form a cycle (`groupsCopy`), so neither function may be bound yet when this module is.
 */
const WORDS: SportPillWords = {
  sportName: (sport) => sportLabel(sport),
  pillLabel: (sport) => sportPillLabel(sport),
  pillHint: COPY.pillHint,
};

/** *+ Another sport*'s words, its press the page's — `PICKER_HINT` read at render, for that cycle. */
function anotherSport(onPress: () => void): AnotherSport {
  return {
    label: COPY.anotherSport,
    drawn: COPY.anotherSportDrawn,
    hint: PICKER_HINT,
    pillHint: COPY.pillHintAnother,
    onPress,
  };
}

export interface SportFilterPageProps {
  /**
   * **What the group plays**, where it says: an official group's declared sports, which the filter
   * narrows to. `undefined` for a player group, and while the group is being read.
   */
  readonly declaredSports?: readonly Sport[];
  /**
   * **The sport a notice opened the page in** (#559) — stood on until the player picks another, and
   * never saved as a pick. Absent for a page opened by the player.
   */
  readonly opening?: Sport;
  /**
   * The page's header, with the pill for its right slot — `undefined` until there is a sport — and
   * `cover`, which the header wraps round what the open bar must cover whole rather than end across:
   * the group's tile. It measures the box it is given against the header's own left edge, so the
   * header draws it as a direct child of a root that spans the page, as `ScreenHeader` does its lead.
   * And the sport the page is on, as the body is handed it: Members' title counts that sport's list.
   */
  readonly header: (
    pill: ReactNode | undefined,
    cover: (node: ReactNode) => ReactNode,
    sport: Sport | undefined,
  ) => ReactNode;
  /**
   * Everything under the header, for the sport the page is on — `undefined` until it is known —
   * and the sports the reader would add to have one here: empty unless the group is an official
   * one they are rated in none of the sports of. And whether the reader meets the door instead —
   * a player group's, rated in nothing (ADR-0200 §2).
   */
  readonly children: (
    sport: Sport | undefined,
    toAdd: readonly Sport[],
    needsALevel: boolean,
  ) => ReactNode;
  /**
   * ***+ Another sport*** was pressed, with the sports it offers — the ones the reader is unrated
   * in (#731). Absent, the bar ends with no such pill.
   */
  readonly onAnother?: (offer: readonly Sport[]) => void;
}

export function SportFilterPage({
  declaredSports,
  opening,
  header,
  children,
  onAnother,
}: SportFilterPageProps) {
  const filter = useGroupSport(declaredSports, opening);
  return (
    <SportFilterFrame
      filter={filter}
      header={header}
      {...(onAnother === undefined ? {} : { onAnother })}
    >
      {children}
    </SportFilterFrame>
  );
}

export interface SportFilterFrameProps extends Omit<
  SportFilterPageProps,
  'declaredSports' | 'opening'
> {
  /** The filter's state — the sports it lists, the one it is on, and picking another. */
  readonly filter: GroupSport;
}

/** **The page around a filter whose state is handed in** — `SportFilterPage`'s drawing. */
export function SportFilterFrame({ filter, header, children, onAnother }: SportFilterFrameProps) {
  const { sports, sport, toAdd, needsALevel, toOffer, choose } = filter;

  // *+ Another sport*: only where the page opens the picker, and only while a sport is left.
  const another =
    onAnother === undefined || toOffer.length === 0
      ? undefined
      : anotherSport(() => onAnother(toOffer));

  return (
    <SportPillFrame
      sports={sports}
      sport={sport}
      onPick={choose}
      words={WORDS}
      {...(another === undefined ? {} : { another })}
      header={(pill, cover) => header(pill, cover, sport)}
    >
      {children(sport, toAdd, needsALevel)}
    </SportPillFrame>
  );
}
