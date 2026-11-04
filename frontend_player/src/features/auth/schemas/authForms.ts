/**
 * Form validation — one canonical schema per form.
 *
 * These are **not** a Zod mirror of the OpenAPI schema. They validate what a player
 * typed, which is a different problem from describing what the backend accepts, and
 * hand-maintaining a runtime copy of every DTO creates two API schemas that drift.
 * See docs/architecture.md Part 9.
 *
 * The constraints that *are* copied — the password length, the nickname's bounds and its
 * pattern — exist so the app can say "that nickname can't contain a space" without a round
 * trip. The server still enforces them; this is a courtesy, never the authority. Where the
 * two disagree the server wins, and the mapped `ValidationError` is what the player sees.
 */

import { z } from 'zod';

/** Trimmed because a leading space is a typo, not an email. Lowercased for the same reason. */
const email = z
  .string()
  .trim()
  .min(1, 'Enter your email address.')
  .email("That doesn't look like an email address.")
  .transform((value) => value.toLowerCase());

export const signInSchema = z.object({
  email,
  // Deliberately only "not empty": a sign-in form must never tell someone their existing
  // password is invalid because the rules changed after they chose it.
  password: z.string().min(1, 'Enter your password.'),
});

export type SignInInput = z.input<typeof signInSchema>;
export type SignInValues = z.output<typeof signInSchema>;

/**
 * The one question on this form that is not about the account.
 *
 * The platform is adults only, and that is a precondition of holding an account rather
 * than a rule about who gets shown to whom
 * ([ADR-0124](../../../../../docs/adr/0124-the-matcher-gates-account-state-never-age.md)).
 * What is collected is an **attestation** — the player's own claim, one boolean — and
 * never a date of birth: there is no date picker here and this is not the ticket that
 * introduces the first one.
 *
 * The label is the claim in the player's own voice, because it is what they are asserting
 * rather than a rule being read at them.
 */
export const ADULT_LABEL = 'I am 18 or over';

/**
 * The sentence for an unanswered age question — **one sentence, shown from two places.**
 *
 * The box refuses before a round trip, and the server refuses again with
 * `adult_attestation_required` on a body this form would not have sent (an older build, a
 * replayed request). Both land under the same control and mean the same thing, so two
 * copies of it would be two sentences to keep in step. `authErrorMessage` reads this one.
 */
export const ADULT_ATTESTATION_MISSING =
  'Confirm that you are 18 or over — Raketa is for adults only.';

/**
 * **The one password rule** — 8 to 128 characters, with at least one letter and one digit — which
 * every account shares (`RawPassword` on the server; ADR-0182 §3). Stated under the box on every
 * form that chooses one, so a refusal never surprises.
 */
export const PASSWORD_RULE = 'Use 8 to 128 characters, with at least one letter and one digit.';

/**
 * A password being **chosen** — on sign-up and on *Set a new password* — under that rule, with
 * the sentence for whichever half is missing. The server's regex counts an ASCII letter and a
 * digit; so does this.
 *
 * Sign-up checked only the length until #515, and a letters-only password there reached the
 * server's rule unchecked; one rule for both forms is what closes that.
 */
const chosenPassword = z
  .string()
  .min(8, 'Use at least 8 characters.')
  .max(128, "That's longer than 128 characters.")
  .regex(/[A-Za-z]/, 'Use at least one letter.')
  .regex(/\d/, 'Use at least one digit.');

const repeatedPassword = z.string().min(1, 'Repeat your password.');

/**
 * The repeat must match — attached to the field the player must fix, not to the form, so the
 * message lands under the box they need to retype.
 */
const SAME_PASSWORD = {
  path: ['confirmPassword'],
  message: "Those passwords don't match.",
};

const samePassword = (values: { readonly password: string; readonly confirmPassword: string }) =>
  values.password === values.confirmPassword;

/**
 * **The Adult attestation, as a form field** — sign-up's and *Start playing*'s. `refine` rather than
 * `z.literal(true)`: an unticked box is `false`, which is a boolean, and only the value is wrong.
 * The message is what a player reads either way, and this is the one that says which of the two it
 * is.
 */
const adultAttested = z.boolean().refine((given) => given, {
  message: ADULT_ATTESTATION_MISSING,
});

/**
 * **Credentials, and nothing about who you are**
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3). The
 * nickname is the naming's, below: sign-up is choosing credentials, and a sign-up refused for a
 * taken handle was a sign-up refused for a reason that had nothing to do with the account. `z.object` strips what it does not name, so a caller still handing one
 * over sends nothing the server would refuse as malformed.
 */
export const signUpSchema = z
  .object({
    email,
    password: chosenPassword,
    confirmPassword: repeatedPassword,
    adultAttested,
  })
  .refine(samePassword, SAME_PASSWORD);

export type SignUpInput = z.input<typeof signUpSchema>;
export type SignUpValues = z.output<typeof signUpSchema>;

/**
 * ***Start playing*'s first step** — the Adult attestation alone, given by an account that already
 * exists: one an Invitation opened, the first time it acts as a player
 * ([ADR-0185](../../../../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
 * §5). The same box and the same sentence as sign-up's, because it is the same claim.
 */
export const adultAttestationSchema = z.object({ adultAttested });

/** Field name -> first message. One message per field is all a form row can show. */
export type FieldErrors = Readonly<Record<string, string>>;

/**
 * Run a schema and return either the parsed values or the per-field messages.
 *
 * Returning both halves of the result as data — rather than throwing — is what lets a
 * screen render errors inline instead of behind a modal.
 */
export function validate<TSchema extends z.ZodTypeAny>(
  schema: TSchema,
  input: unknown,
):
  | { readonly ok: true; readonly values: z.output<TSchema> }
  | { readonly ok: false; readonly fieldErrors: FieldErrors } {
  const result = schema.safeParse(input);
  if (result.success) return { ok: true, values: result.data as z.output<TSchema> };

  const fieldErrors: Record<string, string> = {};
  for (const issue of result.error.issues) {
    const field = issue.path[0];
    // First message wins: a field with three broken rules still has one box to explain.
    if (typeof field === 'string' && fieldErrors[field] === undefined) {
      fieldErrors[field] = issue.message;
    }
  }
  return { ok: false, fieldErrors };
}

/**
 * **The nickname's rule, in the sign-up form's own words** — drawn only as the box's error, when
 * what was typed breaks it, and never as a hint under an empty box: the step is one field, and
 * a sentence under it before anything is typed is clutter for the many who never break it
 * ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md) §3).
 */
export const NICKNAME_RULE = 'Use letters, numbers, and . _ - only — no spaces.';

/**
 * **The naming** — *How should people see you?* — a nickname, and nothing else (ADR-0199 §3).
 *
 * A handle, 2–64 characters of letters, digits and `. _ -`, no spaces, trimmed as the server's
 * value object trims it. Uniqueness is the server's, and its refusal arrives by code under this
 * box. `z.object` strips what it does not name, so a caller still handing a name over sends
 * nothing the server would refuse as malformed.
 */
export const namingSchema = z.object({
  nickname: z
    .string()
    .trim()
    .min(1, 'Enter a nickname.')
    .min(2, 'Nicknames are at least 2 characters.')
    .max(64, 'Nicknames are at most 64 characters.')
    .regex(/^[A-Za-z0-9_.-]+$/, NICKNAME_RULE),
});

export type NamingInput = z.input<typeof namingSchema>;
export type NamingValues = z.output<typeof namingSchema>;

/**
 * ***Forgot password?*** — the address to send a link and a code to
 * ([#515](https://github.com/Raketa02/Raketa/issues/515)). Only its shape is checked: whether it
 * has an account is exactly what nobody may learn from this form (ADR-0184 §5).
 */
export const forgotPasswordSchema = z.object({ email });

/**
 * **The code from the email**, read the way the server reads it — spaces and dashes taken out,
 * upper case — beside the address it was sent to. Its length *is* checked here, where the server
 * does not: a code of the wrong length can only be a wrong code, and five wrong codes lock the
 * email, so one that cannot be right is refused before it spends an attempt.
 */
export const RESET_CODE_LENGTH = 8;

export const resetCodeSchema = z.object({
  email,
  code: z
    .string()
    .transform((typed) => typed.replace(/[\s-]/g, '').toUpperCase())
    .pipe(
      z
        .string()
        .min(1, 'Enter the code from the email.')
        .length(RESET_CODE_LENGTH, `The code is ${RESET_CODE_LENGTH} characters.`),
    ),
});

/**
 * ***Have an invitation code?*** — the same pair, read the same way: an invitation's code is the
 * one credential machinery's (ADR-0184 §4), 8 characters from the same alphabet, and five wrong
 * ones lock it too.
 */
export const invitationCodeSchema = resetCodeSchema;

/** *Set a new password* and *Set your password* — the rule sign-up chooses one by, and the repeat. */
export const newPasswordSchema = z
  .object({ password: chosenPassword, confirmPassword: repeatedPassword })
  .refine(samePassword, SAME_PASSWORD);
