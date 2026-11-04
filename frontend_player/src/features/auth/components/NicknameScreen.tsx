/**
 * **Nickname** — the naming, from a row on the You tab: the box pre-filled, and *Save*
 * ([ADR-0179](../../../../../docs/adr/0179-the-you-tab-is-onboarding-laid-out-flat-and-a-level-is-watched-from-it.md)
 * §7; [ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3 — *at
 * any time, for as long as nobody else holds the new one*).
 *
 * It is the same act as the naming step — `useNamingForm` and `NamingFields`, the same schema,
 * the same mutation and the same sentences — under the tab's chrome instead of the step's:
 * *On your card · Nickname*, a way back, and *Save* where the step says *Continue*. No sentence
 * explains the box; the step's question does not need repeating on a screen that only edits the
 * answer.
 *
 * ## A taken handle is refused by the server, on the press
 *
 * Keeping your own nickname is admitted; another player's comes back `409
 * nickname_already_taken` and is drawn under the box in the app's own words — *That nickname
 * is taken. Pick another.* — exactly as the step draws it. Never a lookup while typing: a
 * handle search is the enumeration ADR-0159 refuses.
 *
 * ## The box opens on the player as read, and the save re-reads it
 *
 * Pre-filled from `GET /users/me`, which bootstrap seeds before the tab can be pressed. The
 * mutation writes what the server recorded into that cache and awaits a fresh read before it
 * resolves, and the form drops what was typed the moment that lands — so the box then shows the
 * re-read, *Save* turns green and says *Saved* on the button's own fade, and the tab's header
 * card and the *Nickname* row already say the new nickname when the player goes back. Everybody
 * else reads it from their next read. **The screen stays**, as every screen behind a row does:
 * the way back is the header's, and a save is not a reason to leave.
 */

import { useRouter } from 'expo-router';

import { ShellScreen, YOU_COPY } from '@/features/shell/types';
import { Button } from '@/shared/ui';

import { useCurrentUser } from '../hooks/useCurrentUser';
import { useNamingForm } from '../hooks/useNamingForm';

import { NamingFields } from './NamingFields';
import { NICKNAME_ROW_TITLE, SAVE_NICKNAME } from './nicknamePresentation';

export function NicknameScreen() {
  const router = useRouter();
  const user = useCurrentUser();

  // A player on the tab is named — the gate holds an account with no nickname at the step and
  // never lets it this far — so the box opens on what they hold; empty only for the shapes the
  // flow cannot produce.
  const form = useNamingForm({ initial: { nickname: user.data?.nickname ?? '' } });

  return (
    <ShellScreen
      eyebrow={YOU_COPY.groups.onYourCard}
      title={NICKNAME_ROW_TITLE}
      onBack={router.back}
      avoidsKeyboard
      action={
        // *Saved*, in green, while the box is as it opened — the button says why it is shut, as
        // the week's does (Part 16, 2026-09-17 and 2026-09-18).
        <Button
          label={form.changed ? SAVE_NICKNAME.label : SAVE_NICKNAME.savedLabel}
          variant={form.changed ? 'primary' : 'settled'}
          size="lg"
          disabled={!form.changed}
          busyLabel={SAVE_NICKNAME.busyLabel}
          busy={form.pending}
          onPress={form.submit}
        />
      }
    >
      <NamingFields form={form} />
    </ShellScreen>
  );
}
