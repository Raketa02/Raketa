/**
 * Form validation — one canonical schema per form.
 *
 * These are **not** a Zod mirror of the OpenAPI schema. They validate what a player
 * typed, which is a different problem from describing what the backend accepts, and
 * hand-maintaining a runtime copy of every DTO creates two API schemas that drift.
 * See docs/architecture.md Part 9.
 *
 * The constraints that *are* copied — the password length, the nickname pattern — exist
 * so the app can say "that nickname can't contain a space" without a round trip. The
 * server still enforces them; this is a courtesy, never the authority. Where the two
 * disagree the server wins, and the mapped `ValidationError` is what the player sees.
 */

import { z } from "zod";

/** Trimmed because a leading space is a typo, not an email. Lowercased for the same reason. */
const email = z
  .string()
  .trim()
  .min(1, "Enter your email address.")
  .email("That doesn't look like an email address.")
  .transform((value) => value.toLowerCase());

export const signInSchema = z.object({
  email,
  // Deliberately only "not empty": a sign-in form must never tell someone their existing
  // password is invalid because the rules changed after they chose it.
  password: z.string().min(1, "Enter your password."),
});

export type SignInInput = z.input<typeof signInSchema>;
export type SignInValues = z.output<typeof signInSchema>;

export const signUpSchema = z
  .object({
    email,
    nickname: z
      .string()
      .trim()
      .min(2, "Nicknames are at least 2 characters.")
      .max(64, "Nicknames are at most 64 characters.")
      .regex(
        /^[A-Za-z0-9_.-]+$/,
        "Use letters, numbers, and . _ - only — no spaces.",
      ),
    password: z
      .string()
      .min(8, "Use at least 8 characters.")
      .max(128, "That's longer than 128 characters."),
    confirmPassword: z.string().min(1, "Repeat your password."),
  })
  .refine((values) => values.password === values.confirmPassword, {
    // Attached to the field the player must fix, not to the form, so the message lands
    // under the box they need to retype.
    path: ["confirmPassword"],
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
    if (typeof field === "string" && fieldErrors[field] === undefined) {
      fieldErrors[field] = issue.message;
    }
  }
  return { ok: false, fieldErrors };
}
