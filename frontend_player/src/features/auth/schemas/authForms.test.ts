/**
 * The two forms' rules, as the player meets them — before a round trip.
 *
 * Every constraint here is a courtesy copy of the server's, so what is pinned is the sentence
 * the player reads and the value that leaves the form, never the server's authority: where
 * the two disagree the server wins, and the mapped error is what the screen shows.
 */

import { NICKNAME_RULE, namingSchema, signUpSchema, validate } from './authForms';

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
