/**
 * The two forms' rules, as the player meets them — before a round trip.
 *
 * Every constraint here is a courtesy copy of the server's, so what is pinned is the sentence
 * the player reads and the value that leaves the form, never the server's authority: where
 * the two disagree the server wins, and the mapped error is what the screen shows.
 */

import {
  NICKNAME_RULE,
  PASSWORD_RULE,
  namingSchema,
  newPasswordSchema,
  resetCodeSchema,
  signUpSchema,
  validate,
} from './authForms';

const CREDENTIALS = {
  email: 'ada@example.com',
  password: 'hunter2hunter2',
  confirmPassword: 'hunter2hunter2',
  adultAttested: true,
};

describe('sign-up', () => {
  /**
   * **Credentials only** ([ADR-0199](../../../../../docs/adr/0199-a-player-is-known-by-their-nickname.md)
   * §3). The nickname is asked in onboarding, and a sign-up form that still took one would be
   * sending a field the server refuses as malformed.
   */
  it('takes email, password and the attestation, and nothing about who you are', () => {
    const result = validate(signUpSchema, CREDENTIALS);

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.values).toEqual({
      email: 'ada@example.com',
      password: 'hunter2hunter2',
      confirmPassword: 'hunter2hunter2',
      adultAttested: true,
    });
    expect(result.values).not.toHaveProperty('nickname');
  });

  it('drops a nickname a caller still sends rather than carrying it to the wire', () => {
    const result = validate(signUpSchema, { ...CREDENTIALS, nickname: 'ada' });

    expect(result.ok).toBe(true);
    if (!result.ok) return;
    expect(result.values).not.toHaveProperty('nickname');
  });
});

describe('the naming', () => {
  it('takes a nickname, and nothing else', () => {
    const result = validate(namingSchema, { nickname: 'ania.k' });

    expect(result).toEqual({ ok: true, values: { nickname: 'ania.k' } });
  });

  it('drops a name a caller still sends rather than carrying it to the wire', () => {
    const result = validate(namingSchema, { name: 'ania.k', nickname: 'ania.k' });

    expect(result).toEqual({ ok: true, values: { nickname: 'ania.k' } });
  });

  it('trims the nickname before checking it', () => {
    expect(validate(namingSchema, { nickname: '  ania.k ' })).toEqual({
      ok: true,
      values: { nickname: 'ania.k' },
    });
  });

  /** The handle's rule, in the sign-up form's own words — the one sentence a broken rule shows. */
  it("refuses a space or a symbol in the rule's own words", () => {
    expect(NICKNAME_RULE).toBe('Use letters, numbers, and . _ - only — no spaces.');
    expect(validate(namingSchema, { nickname: 'ania k' })).toEqual({
      ok: false,
      fieldErrors: { nickname: NICKNAME_RULE },
    });
    expect(validate(namingSchema, { nickname: 'ania@k' })).toEqual({
      ok: false,
      fieldErrors: { nickname: NICKNAME_RULE },
    });
  });

  it('keeps the handle between 2 and 64 characters', () => {
    expect(validate(namingSchema, { nickname: 'a' })).toEqual({
      ok: false,
      fieldErrors: { nickname: 'Nicknames are at least 2 characters.' },
    });
    expect(validate(namingSchema, { nickname: 'a'.repeat(65) })).toEqual({
      ok: false,
      fieldErrors: { nickname: 'Nicknames are at most 64 characters.' },
    });
  });

  it('asks for a nickname when the box is empty', () => {
    expect(validate(namingSchema, { nickname: '' })).toEqual({
      ok: false,
      fieldErrors: { nickname: 'Enter a nickname.' },
    });
  });
});

/**
 * **The one password rule** — 8 to 128 characters with a letter and a digit, every account's
 * (`RawPassword` on the server, ADR-0182 §3) — checked on both forms that choose one, so the
 * sentence a person reads says which half of it they missed.
 */
describe('choosing a password', () => {
  const choose = (password: string, confirmPassword = password) =>
    validate(newPasswordSchema, { password, confirmPassword });

  it('takes one with a letter and a digit in 8 to 128 characters', () => {
    expect(choose('forehand42')).toEqual({
      ok: true,
      values: { password: 'forehand42', confirmPassword: 'forehand42' },
    });
    expect(choose(`a1${'x'.repeat(126)}`).ok).toBe(true);
  });

  it.each([
    ['short1', 'Use at least 8 characters.'],
    [`a1${'x'.repeat(127)}`, "That's longer than 128 characters."],
    ['12345678', 'Use at least one letter.'],
    ['forehands', 'Use at least one digit.'],
  ])('refuses %p, saying which half is missing', (password, message) => {
    expect(choose(password)).toEqual({ ok: false, fieldErrors: { password: message } });
  });

  it('refuses a repeat that does not match, under the repeat box', () => {
    expect(choose('forehand42', 'forehand43')).toEqual({
      ok: false,
      fieldErrors: { confirmPassword: "Those passwords don't match." },
    });
  });

  it('states the rule in one sentence', () => {
    expect(PASSWORD_RULE).toBe('Use 8 to 128 characters, with at least one letter and one digit.');
  });

  /** Sign-up chooses one too, and a letters-only password there is the same refusal. */
  it('is the rule sign-up refuses by', () => {
    expect(
      validate(signUpSchema, {
        ...CREDENTIALS,
        password: 'forehands',
        confirmPassword: 'forehands',
      }),
    ).toEqual({
      ok: false,
      fieldErrors: { password: 'Use at least one digit.' },
    });
  });
});

describe('the code from the email', () => {
  it('reads it the way the server does — no spaces or dashes, upper case', () => {
    expect(validate(resetCodeSchema, { email: 'Tomek@Example.com', code: ' k7m4-qx2p ' })).toEqual({
      ok: true,
      values: { email: 'tomek@example.com', code: 'K7M4QX2P' },
    });
    expect(validate(resetCodeSchema, { email: 'tomek@example.com', code: 'K7M4 QX2P' }).ok).toBe(
      true,
    );
  });

  /**
   * A code of the wrong length is a wrong code, and five wrong codes lock the email — so one that
   * cannot be right is refused here, before it spends an attempt.
   */
  it.each([
    ['', 'Enter the code from the email.'],
    ['K7M4QX2', 'The code is 8 characters.'],
    ['K7M4QX2PP', 'The code is 8 characters.'],
  ])('refuses %p before a round trip', (code, message) => {
    expect(validate(resetCodeSchema, { email: 'tomek@example.com', code })).toEqual({
      ok: false,
      fieldErrors: { code: message },
    });
  });
});
