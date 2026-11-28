/**
 * The profile surface — the read the You tab is drawn from — and the writes that change it.
 *
 * **Ordinary defaults, deliberately.** This is not a ranked list that foregrounding would
 * reorder under the player's finger, so it moves like any other read: a week changed in *You*
 * on another device should be the week this one draws.
 *
 * **The mutations write the response into the cache rather than invalidating it.** Each
 * route answers with the value **as the profile now holds it** — the week in the platform's
 * reading order, the tags in the vocabulary's — so a refetch would be a round trip for an
 * answer already in hand, and Part 7's *"don't immediately refetch what you
 * were just handed"* is the rule. What they must not do is write the number the client *sent*:
 * a client that assumed its own value landed would be re-deciding a bound the server owns.
 * The intro's route answers nothing by design, and its use case says why the line sent is the
 * line held; the two gender writes answer nothing for the same reason and are held the same
 * way.
 *
 * **The three social writes also invalidate the player's own record**
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2): the header card on the You tab draws the face, the intro and the tags off
 * `GET /players/me/record`, which is another feature's read of the same facts — and a tab
 * that read the old line under the name after *Save* would be the one screen the edit was
 * made on saying it did not land. Invalidated, never patched: that read's shape is that
 * feature's, and this one has no business composing it.
 */

import { useMutation, useMutationState, useQuery, useQueryClient } from '@tanstack/react-query';

import { gameKeys } from '@/features/games/types';
import { playerRecordKeys } from '@/features/player_record/types';
import { proposalKeys } from '@/features/proposals/types';
import type { AppError } from '@/shared/errors';
import type { PlayIntent } from '@/shared/vocabulary/playIntent';
import type { SocialTagId } from '@/shared/vocabulary/socialTags';
import type { Sport } from '@/shared/vocabulary/sport';
import type { WeeklyHour } from '@/shared/vocabulary/week';

import type { Gender, GenderPreference } from '../domain/gender';
import type { PlayerProfileSurface } from '../domain/PlayerProfileSurface';
import type { UploadedPhoto } from '../domain/photoCollection';
import { changeWeeklyHours } from '../use-cases/changeWeeklyHours';
import { changeGender } from '../use-cases/changeGender';
import { changeGenderPreference } from '../use-cases/changeGenderPreference';
import { changeIntro } from '../use-cases/changeIntro';
import { changePhotos } from '../use-cases/changePhotos';
import { changeSocialTags } from '../use-cases/changeSocialTags';
import { declarePlayIntent, type PlayIntentDeclaration } from '../use-cases/declarePlayIntent';
import { readProfileSurface } from '../use-cases/readProfileSurface';

import { playerProfileKeys } from './playerProfileKeys';

/** One declaration as the profile now holds it — the pair the write answers with. */
type Declared = { readonly sport: Sport; readonly intent: PlayIntent };

export function useProfileSurface() {
  return useQuery<PlayerProfileSurface, AppError>({
    queryKey: playerProfileKeys.surface(),
    queryFn: ({ signal }) => readProfileSurface({ signal }),
  });
}

/**
 * Replace the profile's week — **the whole grid, and an empty one is a real answer.**
 *
 * The week written into the cache is the **route's**, not the request's: repeated cells are
 * collapsed and the order is the platform's reading order, so a client that kept what it sent
 * would draw a week the profile does not hold.
 *
 * The one caller today is the prompt sheet's *yes* to `KEEP_THESE_TIMES`
 * ([#275](https://github.com/Rakieta02/Rakieta/issues/275)); *You* will be the second.
 */
export function useChangeWeeklyHours() {
  const client = useQueryClient();

  return useMutation<readonly WeeklyHour[], AppError, readonly WeeklyHour[]>({
    mutationFn: (week) => changeWeeklyHours(week),
    onSuccess: (week) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined ? held : { ...held, week },
      );
    },
  });
}

/**
 * Declare what kind of game this player wants in one sport.
 *
 * The pair written into the cache is **the route's answer**, not the request: a declaration
 * that landed is the profile holding it, and that is what the search screen's interstitial
 * reads to close itself. An answer naming a sport or an intent this build cannot read has
 * nothing honest to record, so the read is invalidated instead — the interstitial stays open
 * over a refetch rather than closing over a value nothing can draw.
 */
export function useDeclarePlayIntent() {
  const client = useQueryClient();

  return useMutation<Declared | undefined, AppError, PlayIntentDeclaration>({
    mutationKey: playerProfileKeys.declaring(),
    mutationFn: (declaration) => declarePlayIntent(declaration),
    onSuccess: (declared) => {
      if (declared === undefined) {
        void client.invalidateQueries({ queryKey: playerProfileKeys.surface() });
        return;
      }

      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined
          ? held
          : {
              ...held,
              playIntents: { ...held.playIntents, [declared.sport]: declared.intent },
            },
      );
    },
  });
}

/**
 * **Whether a play intent for this sport is on its way** — a declaration from any screen, read off
 * the mutation's own state rather than a copy of it (#862): the group page's Games tab holds its
 * menu still while one is out, since its answer changes the kinds the deck shows. No sport, none.
 */
export function usePlayIntentOnItsWay(sport: Sport | undefined): boolean {
  const declaring = useMutationState({
    filters: { mutationKey: playerProfileKeys.declaring(), status: 'pending' },
    select: (mutation) => sportDeclared(mutation.state.variables),
  });
  return sport !== undefined && declaring.includes(sport);
}

/** The sport a declaration on its way is for. */
function sportDeclared(asked: unknown): Sport | undefined {
  return typeof asked === 'object' && asked !== null && 'sport' in asked
    ? (asked as PlayIntentDeclaration).sport
    : undefined;
}

/**
 * Replace the profile's Social tags — the You tab's *Save* (ADR-0179 §2).
 *
 * The list written into the cache is the **route's**: the vocabulary's order, whatever order
 * the picker pressed them in, so the picker draws the selection as the profile holds it.
 *
 * **And every read that draws a Social vibe is stale** (ADR-0207 §2, #840): the vibe is worked out
 * from everybody's tags on every read and stored nowhere, so a For-fun card's %, a game's details
 * with your tags' rows — and the Fill in, posting and Friends reads under each group's deck root —
 * and a booked For-fun game's pairing, with its court's vibe (#841), move with the edit.
 * Invalidated, never patched: the number is the server's.
 *
 * **Marked stale, and not read again now** (`refetchType: 'none'`). The server reads everybody's
 * tags from Discovery's directory, a copy the outbox writes after this save has answered — so a deck
 * or details screen still mounted behind the You tab, read again this instant, could be answered
 * from the old tags and hold that answer as fresh for the 30 s `staleTime`. Nothing on screen draws a
 * vibe while the tags are being edited; the next screen that does mounts after the edit — a tab
 * press replaces Play's stack — and `refetchOnMount` reads it then, once the copy has had the
 * seconds it needs. That narrows the window to a player faster than the outbox; it does not close it.
 */
export function useChangeSocialTags() {
  const client = useQueryClient();

  return useMutation<readonly SocialTagId[], AppError, readonly SocialTagId[]>({
    mutationFn: (socialTagIds) => changeSocialTags(socialTagIds),
    onSuccess: (socialTagIds) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined ? held : { ...held, socialTagIds },
      );
      void client.invalidateQueries({ queryKey: playerRecordKeys.all });
      void client.invalidateQueries({ queryKey: proposalKeys.decks(), refetchType: 'none' });
      void client.invalidateQueries({ queryKey: proposalKeys.proposals(), refetchType: 'none' });
      void client.invalidateQueries({ queryKey: gameKeys.pairings(), refetchType: 'none' });
    },
  });
}

/**
 * Replace the profile's photographs, in order — the You tab's write on **every change to the
 * row** (ADR-0179 §2): a promotion, a removal, an upload that landed. Sent by `useOwnPhotos`,
 * which is what decides that a change happened and that one write is in flight at a time.
 *
 * The pairs written into the cache are the route's ids in the route's order, each with the
 * verdict the workbench held — the use case says why the verdicts ride along.
 */
export function useChangePhotos() {
  const client = useQueryClient();

  return useMutation<readonly UploadedPhoto[], AppError, readonly UploadedPhoto[]>({
    mutationFn: (photos) => changePhotos(photos),
    onSuccess: (photos) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined ? held : { ...held, photos },
      );
      void client.invalidateQueries({ queryKey: playerRecordKeys.all });
    },
  });
}

/**
 * Replace the profile's intro, or withdraw it — the You tab's *Save* and *Remove intro*
 * (ADR-0179 §6). `undefined` withdraws.
 *
 * The line written into the cache is the one the use case answers with, and absent where
 * withdrawn — never `''`, because the read never serves one.
 */
export function useChangeIntro() {
  const client = useQueryClient();

  return useMutation<string | undefined, AppError, string | undefined>({
    mutationFn: (line) => changeIntro(line),
    onSuccess: (intro) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) => {
        if (held === undefined) return held;
        const { intro: _withdrawn, ...rest } = held;
        return intro === undefined ? rest : { ...rest, intro };
      });
      void client.invalidateQueries({ queryKey: playerRecordKeys.all });
    },
  });
}

/**
 * Correct the profile's answer to the gender question — the You tab's *Save* under *About
 * you* (ADR-0179 §2). The value written into the cache is the one the use case answers with,
 * which is the value sent; nothing else reads it, so nothing else is invalidated.
 */
export function useChangeGender() {
  const client = useQueryClient();

  return useMutation<Gender, AppError, Gender>({
    mutationFn: (gender) => changeGender(gender),
    onSuccess: (gender) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined ? held : { ...held, gender },
      );
    },
  });
}

/**
 * Change who the profile is matched with — the You tab's *Save* under *Who we should match
 * you with* (ADR-0179 §2). The row's line follows the cache; the gate it changes is evaluated
 * on the next search, on the far side, and nothing here has a cache of that to move.
 */
export function useChangeGenderPreference() {
  const client = useQueryClient();

  return useMutation<GenderPreference, AppError, GenderPreference>({
    mutationFn: (preference) => changeGenderPreference(preference),
    onSuccess: (genderPreference) => {
      client.setQueryData<PlayerProfileSurface>(playerProfileKeys.surface(), (held) =>
        held === undefined ? held : { ...held, genderPreference },
      );
    },
  });
}
