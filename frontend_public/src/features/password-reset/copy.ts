import type { PasswordFormWords } from '@/features/set-password/copy';
import type { LinkState } from '@/features/set-password/mappers';

/**
 * **The reset page's words.** They follow the app's *Forgot password?* where the two say the same
 * thing, by copying it (`frontend_player`'s `resetPresentation.ts`), and send the person to *the
 * app* where the web can't ask again: this site has no *Forgot password?* of its own. None names
 * Raketa: no mock sentence does (ADR-0187 §8).
 */

const ASK_AGAIN = 'To ask again for a new one, open the app and tap “Forgot password?”';

export const RESET_COPY = {
  title: 'Set a new password',
  lead: 'Setting it signs your account out on every phone.',
  /** Once the new password is set here: nobody is signed in (ADR-0187 §4). */
  done: 'New password set. Sign in to the app with your new password.',
} as const;

/** The page's title is the form's, so the form has none of its own. */
export const RESET_FORM: PasswordFormWords = {
  password: 'New password',
  repeat: 'Repeat password',
  submit: 'Set password',
  submitting: 'Setting password…',
};

/** **What a link that no longer works says**, one sentence per state. */
export const RESET_STATES: Readonly<Record<Exclude<LinkState, 'valid'>, string>> = {
  expired: `That link has expired. ${ASK_AGAIN}`,
  used: 'That link has already been used. Sign in to the app with your new password, or ask again for a new one.',
  locked: `Too many wrong codes were typed for that email, so its link is locked too. ${ASK_AGAIN}`,
};

/** The form's own refusal, beside the password rule's: a token that could be nobody's. */
export const RESET_REFUSALS: Readonly<Record<string, string>> = {
  credential_not_found: `That link isn't one we sent. ${ASK_AGAIN}`,
};
