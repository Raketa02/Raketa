import {
  SETUP_START,
  advance,
  canContinue,
  setupSteps,
  waysToPay,
  wordsInForce,
  type SetupEvent,
  type SetupProgress,
} from './setupSteps';

/** Walk a run of events from the start, as a player presses through the checklist. */
function walk(...events: readonly SetupEvent[]): SetupProgress {
  return events.reduce(advance, SETUP_START);
}

/** The four steps as `name:state`, in the order the card draws them. */
function drawn(progress: SetupProgress): readonly string[] {
  return setupSteps(progress).map((step) => `${step.name}:${step.state}`);
}

describe('the order (Q82) — choose, card details, the terms, the bank', () => {
  it('opens on step 1 with the other three waiting, numbered 1 to 4', () => {
    expect(drawn(SETUP_START)).toEqual([
      'choose:open',
      'card:waiting',
      'terms:waiting',
      'bank:waiting',
    ]);
    expect(setupSteps(SETUP_START).map((step) => step.number)).toEqual([1, 2, 3, 4]);
  });

  it('walks a card through all four, each finished step done', () => {
    const chosen = walk({ type: 'chose', payWith: 'CARD' }, { type: 'continued' });
    expect(drawn(chosen)).toEqual(['choose:done', 'card:open', 'terms:waiting', 'bank:waiting']);

    const saved = advance(chosen, { type: 'cardSaved' });
    expect(drawn(saved)).toEqual(['choose:done', 'card:done', 'terms:open', 'bank:waiting']);

    const accepted = advance(saved, { type: 'termsAccepted' });
    expect(drawn(accepted)).toEqual(['choose:done', 'card:done', 'terms:done', 'bank:open']);
  });

  it('never opens the bank before the terms: the secret is the answer to them', () => {
    const saved = walk(
      { type: 'chose', payWith: 'CARD' },
      { type: 'continued' },
      { type: 'cardSaved' },
    );
    expect(saved.open).toBe('terms');
  });
});

describe('a wallet skips the card details', () => {
  it('goes from the choice straight to the terms, step 2 marked skipped', () => {
    const chosen = walk({ type: 'chose', payWith: 'GOOGLE_PAY' }, { type: 'continued' });
    expect(drawn(chosen)).toEqual(['choose:done', 'card:skipped', 'terms:open', 'bank:waiting']);
    expect(drawn(advance(chosen, { type: 'termsAccepted' }))).toEqual([
      'choose:done',
      'card:skipped',
      'terms:done',
      'bank:open',
    ]);
  });

  it('is only skipped once the wallet is the answer — while choosing, step 2 waits', () => {
    expect(drawn(walk({ type: 'chose', payWith: 'APPLE_PAY' }))).toEqual([
      'choose:open',
      'card:waiting',
      'terms:waiting',
      'bank:waiting',
    ]);
  });

  it('ignores a card saved while no card step is open', () => {
    const chosen = walk({ type: 'chose', payWith: 'GOOGLE_PAY' }, { type: 'continued' });
    expect(advance(chosen, { type: 'cardSaved' })).toBe(chosen);
  });
});

describe('BLIK is offered and cannot continue', () => {
  it('refuses Continue with BLIK chosen, and with nothing chosen', () => {
    expect(canContinue('BLIK')).toBe(false);
    expect(canContinue(null)).toBe(false);
    expect(canContinue('CARD')).toBe(true);
    expect(canContinue('GOOGLE_PAY')).toBe(true);
    expect(canContinue('APPLE_PAY')).toBe(true);

    const blik = walk({ type: 'chose', payWith: 'BLIK' });
    expect(advance(blik, { type: 'continued' })).toBe(blik);
    expect(advance(SETUP_START, { type: 'continued' })).toBe(SETUP_START);
  });

  it('lets the choice change while step 1 is open', () => {
    const changed = walk({ type: 'chose', payWith: 'BLIK' }, { type: 'chose', payWith: 'CARD' });
    expect(changed.chosen).toBe('CARD');
    expect(advance(changed, { type: 'continued' }).open).toBe('card');
  });
});

describe('when the bank refuses the card', () => {
  const atTheBank = walk(
    { type: 'chose', payWith: 'CARD' },
    { type: 'continued' },
    { type: 'cardSaved' },
    { type: 'termsAccepted' },
  );

  it('reopens the card details and keeps the terms — the same setup can try another card', () => {
    const declined = advance(atTheBank, { type: 'declined' });
    expect(drawn(declined)).toEqual(['choose:done', 'card:open', 'terms:done', 'bank:waiting']);
    // The next card goes straight to the bank: the terms were accepted for this setup.
    expect(advance(declined, { type: 'cardSaved' }).open).toBe('bank');
  });

  it('sends a refused wallet back to the choice', () => {
    const wallet = walk(
      { type: 'chose', payWith: 'GOOGLE_PAY' },
      { type: 'continued' },
      { type: 'termsAccepted' },
    );
    expect(advance(wallet, { type: 'declined' }).open).toBe('choose');
  });
});

describe('going back', () => {
  it('reopens the choice from a later step, forgetting the card and keeping the terms', () => {
    const atTheTerms = walk(
      { type: 'chose', payWith: 'CARD' },
      { type: 'continued' },
      { type: 'cardSaved' },
      { type: 'termsAccepted' },
    );
    const reopened = advance(atTheTerms, { type: 'reopened' });
    expect(reopened).toEqual({
      open: 'choose',
      chosen: 'CARD',
      cardSaved: false,
      termsAccepted: true,
    });
    // A wallet now goes straight to the bank.
    expect(
      walk(
        { type: 'chose', payWith: 'CARD' },
        { type: 'continued' },
        { type: 'cardSaved' },
        { type: 'termsAccepted' },
        { type: 'reopened' },
        { type: 'chose', payWith: 'GOOGLE_PAY' },
        { type: 'continued' },
      ).open,
    ).toBe('bank');
  });

  it('starts over when the setup is gone at the server, keeping only the choice', () => {
    const atTheBank = walk(
      { type: 'chose', payWith: 'CARD' },
      { type: 'continued' },
      { type: 'cardSaved' },
      { type: 'termsAccepted' },
    );
    expect(advance(atTheBank, { type: 'startedOver' })).toEqual({ ...SETUP_START, chosen: 'CARD' });
  });
});

describe('what step 1 offers, and which words Accept agrees to', () => {
  it('offers a card and BLIK, and the phone’s own wallet only when it has one', () => {
    expect(waysToPay(null)).toEqual(['CARD', 'BLIK']);
    expect(waysToPay('GOOGLE_PAY')).toEqual(['CARD', 'BLIK', 'GOOGLE_PAY']);
    expect(waysToPay('APPLE_PAY')).toEqual(['CARD', 'BLIK', 'APPLE_PAY']);
  });

  it('holds the words shown to the terms in force, once a setup has named them', () => {
    expect(wordsInForce('2026-09-29', null)).toBe(true);
    expect(wordsInForce('2026-09-29', '2026-09-29')).toBe(true);
    expect(wordsInForce('2026-09-29', '2026-10-15')).toBe(false);
  });
});
