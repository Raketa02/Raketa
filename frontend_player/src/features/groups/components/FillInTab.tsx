/**
 * **Fill in, with nothing in it** — one dark card saying what the tab will be for, with the link's
 * two doors (play 45–47; PRD #500 stories 66–67). Since #557 the tab is `proposals`' board, and this
 * is what it draws while there is no seat to fill and no yes of the reader's waiting.
 *
 * *No games yet — it's just you* while the player is the group's only member, and *No games yet*
 * once anybody else has joined: whether it is *just you* is a count of **members**, not of people
 * rated in the sport, because a game posted here is seen by everybody who arrives with the link.
 *
 * **+ Post a game is drawn and does nothing** (ADR-0183 §13) — `PostAGame` below, which the page
 * floats over its bottom corner. It is the primary button, disabled: the one coral door on the page
 * is the one that cannot be opened yet, and the system's dim and `disabled` state say so to the eye
 * and to a listener, where a full-strength button that ignored its press would say the opposite.
 */

import { Button } from '@/shared/ui';

import type { Group } from '../domain/group';

import { GROUPS_COPY } from './groupsCopy';
import { LinkCard } from './LinkCard';

const COPY = GROUPS_COPY.fillIn;

export function FillInTab({ group }: { readonly group: Group }) {
  return (
    <LinkCard
      group={group}
      headline={group.memberCount > 1 ? COPY.others : COPY.alone}
      line={COPY.line}
    />
  );
}

/** *+ Post a game* — drawn, inert, and said to be so. The page places it. */
export function PostAGame() {
  return (
    <Button
      label={COPY.postAGameDrawn}
      accessibilityLabel={COPY.postAGame}
      size="lg"
      disabled
      onPress={() => undefined}
    />
  );
}
