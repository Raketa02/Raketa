/**
 * **Your week** — the availability grid as the step draws it, a draft until *Save your week*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §2).
 *
 * The grid is `WeekGrid`, exactly as `SocialAvailabilityStep` draws it: days down, parts of the
 * day across, the mint tick — with the one thing the step cut and this screen was written for,
 * the footnote inside the card that counts the slots and says what a blank week means. Under
 * the card, *Save your week* and *Clear all*.
 *
 * ## A draft until the button
 *
 * The grid opens on the week the profile holds and every press moves a draft of it; nothing
 * is written on a press. *Save your week* sends one `PUT /players/me/availability` carrying the
 * whole week, and what the screen then draws is **the route's answer** written into the cache
 * — repeated cells collapsed, the platform's reading order — never the draft echoed back. The
 * draft is dropped the moment the save lands, so the grid and the row's live line are then
 * one read. The button is shut while the draft is the week already held — and **green, saying
 * *Saved***: a save that changes nothing is a round trip for an answer in hand, and the
 * button's state is the message (6.1 `settled`). It turns green as the save lands, on the
 * button's own fade, and is simply green on a screen opened with nothing to save.
 *
 * ## An empty week is a legal value here
 *
 * The commit's floor of one slot does not bind: `AvailabilityGridEmpty` binds the answer a
 * player is *asked for* at the end of onboarding, and a player who unticks every cell
 * afterwards has said something legal, which the matcher reads as *absent* rather than as a
 * zero ([ADR-0102](../../../../../docs/adr/0102-silence-is-never-scored.md)). So *Clear all*
 * is offered and *Save your week* is open on an empty draft, and the footnote says what the
 * empty week means.
 */

import { useRouter } from 'expo-router';
import { useState } from 'react';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { recoveryMessage } from '@/shared/errors';
import { Button, Note } from '@/shared/ui';

import type { AvailabilitySlot } from '../domain/ProfileDraft';
import { sameWeek, toggleCell, weekStanding } from '../domain/availabilityWeek';
import { useChangeAvailability, useProfileSurface } from '../hooks/useProfileSurface';

import { availabilityFootnote } from './availabilityPresentation';
import { ProfileReadStanding } from './ProfileReadStanding';
import { WeekGrid } from './WeekGrid';
import {
  CLEAR_ALL,
  LOADING_WEEK,
  SAVED,
  SAVE_YOUR_WEEK,
  SAVING,
  YOUR_WEEK_TITLE,
} from './youProfilePresentation';

export function YourWeekScreen() {
  const router = useRouter();
  const profile = useProfileSurface();
  const save = useChangeAvailability();
  /** The week as the player has left it — `undefined` while it is the profile's own. */
  const [draft, setDraft] = useState<readonly AvailabilitySlot[]>();

  const held = profile.data?.week;
  const week = draft ?? held;
  const dirty = held !== undefined && draft !== undefined && !sameWeek(draft, held);

  const press = (cell: AvailabilitySlot) => {
    if (week === undefined) return;
    setDraft(toggleCell(week, cell));
  };

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.findingPlayers}
      title={YOUR_WEEK_TITLE}
      onBack={router.back}
      action={
        week === undefined ? undefined : (
          <>
            {save.error !== null ? (
              <Note variant="coral" accessibilityRole="alert">
                {recoveryMessage(save.error)}
              </Note>
            ) : null}
            <Button
              label={dirty ? SAVE_YOUR_WEEK : SAVED}
              variant={dirty ? 'primary' : 'settled'}
              size="lg"
              disabled={!dirty}
              busy={save.isPending}
              busyLabel={SAVING}
              onPress={() =>
                // The cache holds the route's week by the time this runs; dropping the draft
                // is what lets the grid draw it.
                save.mutate(week, { onSuccess: () => setDraft(undefined) })
              }
            />
            <Button
              label={CLEAR_ALL}
              variant="secondary"
              size="lg"
              disabled={weekStanding(week).kind === 'empty' || save.isPending}
              onPress={() => setDraft([])}
            />
          </>
        )
      }
    >
      <ProfileReadStanding
        fetchStatus={profile.fetchStatus}
        isPending={profile.isPending}
        error={profile.error}
        onRetry={() => void profile.refetch()}
        loadingLabel={LOADING_WEEK}
      />

      {week === undefined ? null : (
        <WeekGrid
          week={week}
          onPressCell={press}
          footnote={availabilityFootnote(weekStanding(week))}
        />
      )}
    </ShellScreen>
  );
}
