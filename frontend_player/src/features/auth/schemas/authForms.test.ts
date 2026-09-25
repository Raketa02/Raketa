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
   * **Credentials only** ([ADR-0171](../../../../../docs/adr/0171-a-player-has-a-name-and-a-nickname-and-the-name-is-what-is-said.md)
   * §2). The nickname is asked in onboarding, beside the name, and a sign-up form that still
   * took one would be sending a field the server now refuses as malformed.
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
  it('takes a name with spaces in it, and the handle beside it', () => {
    const result = validate(namingSchema, { name: 'Ania Kowalska', nickname: 'ania_k' });

    expect(result).toEqual({ ok: true, values: { name: 'Ania Kowalska', nickname: 'ania_k' } });
  });

  /**
   * The server trims and collapses before it checks the bounds
   * (`NameRequest`'s own note), and the form does the same so the sentence it shows is about
   * the name that would leave it: `"   A   "` is one character, not seven.
   */
  it('trims the name and collapses runs of whitespace before checking its length', () => {
    const roomy = validate(namingSchema, { name: '  Ania   Kowalska ', nickname: 'ania_k' });
    expect(roomy).toEqual({ ok: true, values: { name: 'Ania Kowalska', nickname: 'ania_k' } });

    const short = validate(namingSchema, { name: '   A   ', nickname: 'ania_k' });
    expect(short).toEqual({ ok: false, fieldErrors: { name: 'Names are at least 2 characters.' } });
  });

  it('asks for a name when the box is empty', () => {
    expect(validate(namingSchema, { name: '', nickname: 'ania_k' })).toEqual({
      ok: false,
      fieldErrors: { name: 'Enter your name.' },
    });
  });

  it('refuses a name longer than 64 characters', () => {
    expect(validate(namingSchema, { name: 'a'.repeat(65), nickname: 'ania_k' })).toEqual({
      ok: false,
      fieldErrors: { name: 'Names are at most 64 characters.' },
    });
  });

  it('never checks a name against anybody, and takes one word alone', () => {
    expect(validate(namingSchema, { name: 'Dieguito', nickname: 'diego_f' })).toEqual({
      ok: true,
      values: { name: 'Dieguito', nickname: 'diego_f' },
    });
  });

  /** The handle's rule is the sign-up form's own words, moved here with the field. */
  it("states the nickname's rule under its field, in the sign-up form's words", () => {
    expect(NICKNAME_RULE).toBe('Use letters, numbers, and . _ - only — no spaces.');
    expect(validate(namingSchema, { name: 'Ania Kowalska', nickname: 'ania k' })).toEqual({
      ok: false,
      fieldErrors: { nickname: NICKNAME_RULE },
    });
  });

  it('keeps the handle between 2 and 64 characters', () => {
    expect(validate(namingSchema, { name: 'Ania Kowalska', nickname: 'a' })).toEqual({
      ok: false,
      fieldErrors: { nickname: 'Nicknames are at least 2 characters.' },
    });
    expect(validate(namingSchema, { name: 'Ania Kowalska', nickname: 'a'.repeat(65) })).toEqual({
      ok: false,
      fieldErrors: { nickname: 'Nicknames are at most 64 characters.' },
    });
  });

  it('says what is missing under each box at once', () => {
    expect(validate(namingSchema, { name: '', nickname: '' })).toEqual({
      ok: false,
      fieldErrors: { name: 'Enter your name.', nickname: 'Enter a nickname.' },
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
