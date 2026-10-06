/**
 * **Name** — the naming, from a row on the You tab: the two boxes pre-filled, and *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7; the follow-up [ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * left open).
 *
 * It is the same act as the naming step — `useNamingForm` and `NamingFields`, the same schema,
 * the same mutation and the same sentences — under the tab's chrome instead of the step's:
 * *On your card · Name*, a way back, and *Save* where the step says *Continue*. No sentence
 * explains the two boxes; the step's question does not need repeating on a screen that only
 * edits the answer.
 *
 * ## A taken handle is refused by the server, on the press
 *
 * Keeping your own nickname is admitted; another player's comes back `409
 * nickname_already_taken` and is drawn under the box in the app's own words — *That nickname
 * is taken. Pick another.* — exactly as the step draws it. Never a lookup while typing: a
 * handle search is the enumeration ADR-0159 refuses.
 *
 * ## The boxes open on the player as read, and the save re-reads them
 *
 * Pre-filled from `GET /users/me`, which bootstrap seeds before the tab can be pressed. The
 * mutation writes what the server recorded into that cache and awaits a fresh read before it
 * resolves (ADR-0171 §3), and the form drops what was typed the moment that lands — so the
 * boxes then show the re-read, *Save* turns green and says *Saved* on the button's own fade,
 * and the tab's header card and the *Name* row already say the new name when the player goes
 * back. **The screen stays**, as every screen behind a row does: the way back is the header's,
 * and a save is not a reason to leave.
 */

import { useRouter } from 'expo-router';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { Button } from '@/shared/ui';

import { useCurrentUser } from '../hooks/useCurrentUser';
import { useNamingForm } from '../hooks/useNamingForm';

import { NamingFields } from './NamingFields';
import { NAME_ROW_TITLE, SAVE_NAME } from './namePresentation';

export function NameScreen() {
  const router = useRouter();
  const user = useCurrentUser();

  // A player on the tab is named — the gate holds an unnamed account at the step and never
  // lets it this far — so the boxes open on what they hold; empty only for the shapes the
  // flow cannot produce.
  const form = useNamingForm({
    initial: { name: user.data?.name ?? '', nickname: user.data?.nickname ?? '' },
  });

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.onYourCard}
      title={NAME_ROW_TITLE}
      onBack={router.back}
      avoidsKeyboard
      action={
        // *Saved*, in green, while the boxes are as they opened — the button says why it is
        // shut, as the week's does (Part 16, 2026-09-17 and 2026-09-18).
        <Button
          label={form.changed ? SAVE_NAME.label : SAVE_NAME.savedLabel}
          variant={form.changed ? 'primary' : 'settled'}
          size="lg"
          disabled={!form.changed}
          busyLabel={SAVE_NAME.busyLabel}
          busy={form.pending}
          onPress={form.submit}
        />
      }
    >
      <NamingFields form={form} />
    </ShellScreen>
  );
}
