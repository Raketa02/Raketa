/**
 * *N yeses to give*, and the one rule the client pre-empts the server on — **at the ceiling a
 * stranger's card settles and a liker's card flies** — written where somebody could get it
 * wrong: a yes that closes a mutual is never outstanding, so the cap does not apply to it
 * ([ADR-0169](../../../../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
 * §3).
 */

import { yesWithheld, yesesToGive } from './yesBudget';

describe('yeses to give', () => {
  it('is the cap less what is outstanding, both read off the wire', () => {
    expect(yesesToGive({ cap: 20, outstanding: 8 })).toBe(12);
    expect(yesesToGive({ cap: 20, outstanding: 20 })).toBe(0);
  });

  /** The cap is ruleset configuration and may come down between releases, under a standing count. */
  it('never goes below nought when the cap has moved under the count', () => {
    expect(yesesToGive({ cap: 10, outstanding: 12 })).toBe(0);
  });
});

describe('withholding a yes at the ceiling', () => {
  it('withholds a stranger’s yes when there is none to give', () => {
    expect(yesWithheld({ give: 0 })).toBe(true);
  });

  it('sends a liker’s yes whatever the count, because it closes a mutual and gives the slot back', () => {
    expect(yesWithheld({ give: 0, inclusionReason: 'INTEREST_LIFT' })).toBe(false);
  });

  it('sends every yes while there are some to give', () => {
    expect(yesWithheld({ give: 1 })).toBe(false);
    expect(yesWithheld({ give: 12, inclusionReason: 'INTEREST_LIFT' })).toBe(false);
  });

  /**
   * The count comes off a read that may not have landed, and the server is the authority: a
   * `409` still returns the card. With no count the client pre-empts nothing.
   */
  it('withholds nothing before the count has landed', () => {
    expect(yesWithheld({ give: undefined })).toBe(false);
  });
});
