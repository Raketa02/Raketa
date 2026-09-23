/**
 * Form validation — one canonical schema per form.
 *
 * These are **not** a Zod mirror of the OpenAPI schema. They validate what a player
 * typed, which is a different problem from describing what the backend accepts, and
 * hand-maintaining a runtime copy of every DTO creates two API schemas that drift.
 * See docs/architecture.md Part 9.
 *
 * The constraints that *are* copied — the password length, the name's bounds, the nickname
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
 * **Credentials, and nothing about who you are**
 * ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
 * §2). The nickname left this form for the naming below: sign-up is choosing credentials, and
 * a sign-up refused for a taken handle was a sign-up refused for a reason that had nothing to
 * do with the account. `z.object` strips what it does not name, so a caller still handing one
 * over sends nothing the server would refuse as malformed.
 */
export const signUpSchema = z
  .object({
    email,
    password: z
      .string()
      .min(8, 'Use at least 8 characters.')
      .max(128, "That's longer than 128 characters."),
    confirmPassword: z.string().min(1, 'Repeat your password.'),
    // `refine` rather than `z.literal(true)`: an unticked box is `false`, which is a
    // boolean, and only the value is wrong. The message is what a player reads either
    // way, and this is the one that says which of the two it is.
    adultAttested: z.boolean().refine((given) => given, {
      message: ADULT_ATTESTATION_MISSING,
    }),
  })
  .refine((values) => values.password === values.confirmPassword, {
    // Attached to the field the player must fix, not to the form, so the message lands
    // under the box they need to retype.
    path: ['confirmPassword'],
    message: "Those passwords don't match.",
  });

export type SignUpInput = z.input<typeof signUpSchema>;
export type SignUpValues = z.output<typeof signUpSchema>;

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
 * **The nickname's rule, in the sign-up form's own words** — stated under the box on the
 * naming step as well as being the sentence a refusal shows, so a player is told what a handle
 * may contain before a refusal ever surprises them (ADR-0171 §1).
 */
export const NICKNAME_RULE = 'Use letters, numbers, and . _ - only — no spaces.';

/**
 * **The naming** — *How should people see you?* — a name and a nickname, both required.
 *
 * The **name** is trimmed and its runs of whitespace collapsed to one space *before* the bounds
 * are checked, exactly as the server's value object normalises it: `"   A   "` is one character
 * and is refused as too short here rather than admitted and refused there. It is checked against
 * nobody — two players may share one.
 *
 * The **nickname** keeps the rule the sign-up form used to state: a handle, 2–64 characters of
 * letters, digits and `. _ -`, no spaces. Uniqueness is the server's, and its refusal arrives by
 * code under this box.
 */
export const namingSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, 'Enter your name.')
    .transform((value) => value.replace(/\s+/g, ' '))
    .pipe(
      z
        .string()
        .min(2, 'Names are at least 2 characters.')
        .max(64, 'Names are at most 64 characters.'),
    ),
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
