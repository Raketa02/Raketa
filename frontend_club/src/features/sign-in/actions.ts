'use server';

import { redirect } from 'next/navigation';

import { checkDetails, detailsOf, readDetails } from '@/features/club-details/schemas';
import { anonymously, beginSession, signOutClub } from '@/server/club';
import type { ApiError } from '@/server/outcome';
import { endRecovery, readRecovery, saveRecovery } from '@/server/recovery';
import { formText, hasRefusals, placeRefusal, type FormState, type Refusals } from '@/ui/forms';

import { toSignUpBody } from './mappers';
import {
  ASK_FIELDS,
  checkChosenPassword,
  checkCode,
  checkEmail,
  checkTypedPassword,
  CODE_FIELDS,
  isPlausibleToken,
  isSendablePassword,
  NEW_PASSWORD_FIELDS,
  normaliseCode,
  SIGN_IN_FIELDS,
  SIGN_UP_FIELDS,
  type AskField,
  type CodeField,
  type NewPasswordField,
  type SignInField,
  type SignUpField,
} from './schemas';

/**
 * **The signed-out acts, and signing out.** Each one checks what it can before anything leaves,
 * then asks the backend, then answers the form with codes; a success leaves by `redirect`.
 */

const OVERVIEW = '/overview';

/**
 * A `422` on a form whose one box the contract checks by format is the email (`format: email`):
 * the backend's own email check disagreed with this one, so it is the email's refusal.
 */
function asEmailRefusal(error: ApiError): ApiError {
  return error.code === 'request_invalid'
    ? { ...error, code: 'email_invalid', field: 'email' }
    : error;
}
const PASSWORD_SET = '/overview?notice=password-set';

export async function signIn(
  _previous: FormState<SignInField>,
  form: FormData,
): Promise<FormState<SignInField>> {
  const email = formText(form, 'email').trim();
  const password = formText(form, 'password');

  const refusals: Refusals<SignInField> = {};
  const emailRefusal = checkEmail(email);
  if (emailRefusal !== null) refusals.email = emailRefusal;
  const passwordRefusal = checkTypedPassword(password);
  if (passwordRefusal !== null) refusals.password = passwordRefusal;
  if (hasRefusals(refusals)) return { refusals, formRefusal: null };
  // No club's password is longer than an account allows; the backend would only call the
  // request malformed.
  if (!isSendablePassword(password)) {
    return { refusals: {}, formRefusal: 'invalid_credentials' };
  }

  const outcome = await anonymously((api) =>
    api.POST('/api/v1/club/auth/login', { body: { email, password } }),
  );
  if (!outcome.ok) return placeRefusal(asEmailRefusal(outcome.error), SIGN_IN_FIELDS);

  await beginSession(outcome.data);
  redirect(OVERVIEW);
}

/**
 * **Sign up**: the club and its account in one request, then signed straight in with the
 * credentials just chosen, because sign-up itself issues no tokens.
 */
export async function signUp(
  _previous: FormState<SignUpField>,
  form: FormData,
): Promise<FormState<SignUpField>> {
  const draft = readDetails(form);
  const email = formText(form, 'email').trim();
  const password = formText(form, 'password');

  const refusals: Refusals<SignUpField> = { ...checkDetails(draft) };
  const emailRefusal = checkEmail(email);
  if (emailRefusal !== null) refusals.email = emailRefusal;
  const passwordRefusal = checkChosenPassword(password);
  if (passwordRefusal !== null) refusals.password = passwordRefusal;
  if (hasRefusals(refusals) || draft.point === null) return { refusals, formRefusal: null };

  const body = toSignUpBody(detailsOf({ ...draft, point: draft.point }), email, password);
  const created = await anonymously((api) => api.POST('/api/v1/club/sign-up', { body }));
  if (!created.ok) return placeRefusal(created.error, SIGN_UP_FIELDS);

  const signedIn = await anonymously((api) =>
    api.POST('/api/v1/club/auth/login', { body: { email, password } }),
  );
  // The club exists either way; if its first sign-in did not go through, sign-in says so.
  if (!signedIn.ok) redirect('/sign-in?signed-up=1');

  await beginSession(signedIn.data);
  redirect(OVERVIEW);
}

export async function signOut(): Promise<void> {
  await signOutClub();
  redirect('/sign-in');
}

// --- Forgot password? ---------------------------------------------------------

export interface AskState extends FormState<AskField> {
  /** The address the email went to, or `null` until one did. */
  readonly sentTo: string | null;
}

/**
 * **Ask for a link and a code.** The backend answers `202` whether or not the address signs a
 * club in, and the page says one sentence either way, so nobody learns from it who does.
 */
export async function askForReset(_previous: AskState, form: FormData): Promise<AskState> {
  const email = formText(form, 'email').trim();
  const refusal = checkEmail(email);
  if (refusal !== null) return { refusals: { email: refusal }, formRefusal: null, sentTo: null };

  const outcome = await anonymously((api) =>
    api.POST('/api/v1/club/auth/forgot-password', { body: { email } }),
  );
  if (!outcome.ok) {
    return {
      ...placeRefusal(asEmailRefusal(outcome.error), ASK_FIELDS),
      sentTo: null,
    };
  }

  await saveRecovery({ email });
  return { refusals: {}, formRefusal: null, sentTo: email };
}

/**
 * **Claim the emailed code** for a ticket, which is kept server-side in the recovery cookie and
 * spent by *Set a new password*. A claim is not a use: the same code can be claimed again.
 */
export async function claimCode(
  _previous: FormState<CodeField>,
  form: FormData,
): Promise<FormState<CodeField>> {
  const email = formText(form, 'email').trim();
  const typed = formText(form, 'code');

  const refusals: Refusals<CodeField> = {};
  const emailRefusal = checkEmail(email);
  if (emailRefusal !== null) refusals.email = emailRefusal;
  const codeRefusal = checkCode(typed);
  if (codeRefusal !== null) refusals.code = codeRefusal;
  if (hasRefusals(refusals)) return { refusals, formRefusal: null };

  const outcome = await anonymously((api) =>
    api.POST('/api/v1/club/auth/forgot-password/claim', {
      body: { email, code: normaliseCode(typed) },
    }),
  );
  if (!outcome.ok) return placeRefusal(asEmailRefusal(outcome.error), CODE_FIELDS);

  await saveRecovery({ email, ticket: outcome.data.ticket }, outcome.data.expires_in);
  redirect('/forgot-password/new-password');
}

type NewPasswordState = FormState<NewPasswordField>;

async function setNewPassword(
  way: { readonly token: string } | { readonly ticket: string },
  form: FormData,
): Promise<NewPasswordState> {
  const password = formText(form, 'password');
  const refusal = checkChosenPassword(password);
  if (refusal !== null) return { refusals: { password: refusal }, formRefusal: null };

  const outcome = await anonymously((api) =>
    api.POST('/api/v1/club/auth/forgot-password/new-password', { body: { ...way, password } }),
  );
  if (!outcome.ok) return placeRefusal(outcome.error, NEW_PASSWORD_FIELDS);

  // Setting it signed every other browser out and this one in (ADR-0185 §7).
  await beginSession(outcome.data);
  await endRecovery();
  redirect(PASSWORD_SET);
}

/** *Set a new password* after a claimed code: the ticket comes from the recovery cookie. */
export async function setPasswordByCode(
  _previous: NewPasswordState,
  form: FormData,
): Promise<NewPasswordState> {
  const recovery = await readRecovery();
  if (recovery?.ticket === undefined) return { refusals: {}, formRefusal: 'ticket_missing' };
  return setNewPassword({ ticket: recovery.ticket }, form);
}

/** *Set a new password* from the email's link, `/reset/<token>`: the token is bound per page. */
export async function setPasswordByLink(
  token: string,
  _previous: NewPasswordState,
  form: FormData,
): Promise<NewPasswordState> {
  if (!isPlausibleToken(token)) return { refusals: {}, formRefusal: 'credential_not_found' };
  return setNewPassword({ token }, form);
}
