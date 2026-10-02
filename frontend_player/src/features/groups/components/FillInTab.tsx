/**
 * **Fill in, with nothing in it** — one dark card saying what the tab will be for, with the link's
 * two doors (play 45–47; PRD #500 stories 66–67). Since #557 the tab is `proposals`' board, and this
 * is what it draws while there is no seat to fill and no yes of the reader's waiting.
 *
 * *No games yet — it's just you* while the player is the group's only member, and *No games yet*
 * once anybody else has joined: whether it is *just you* is a count of **members**, not of people
 * rated in the sport, because a game posted here is seen by everybody who arrives with the link.
 *
 * **+ Post a game opens *Post a game*** (#558; the screens A5) — `PostAGame` below, which the page
 * floats over its bottom corner and *Nothing picked right now* carries as its third door. It is the
 * primary button: the one coral door on the page. Until #558 it was drawn disabled, because posting
 * had not shipped (ADR-0183 §13, superseded there by ADR-0189).
 */

import { router } from 'expo-router';

import { postAGameRoute } from '@/features/proposals/types';
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

/** *+ Post a game* — pushes the screen over the group's page. The page places it. */
export function PostAGame({ groupId }: { readonly groupId: string }) {
  return (
    <Button
      label={COPY.postAGameDrawn}
      accessibilityLabel={COPY.postAGame}
      size="lg"
      onPress={() => router.push(postAGameRoute(groupId))}
    />
  );
}
