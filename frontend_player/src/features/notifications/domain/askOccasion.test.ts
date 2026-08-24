import { explainAtStandbyJoin, promptIsAvailable } from './askOccasion';

describe('whether spending the OS prompt can still buy anything', () => {
  it('is available on a fresh install', () => {
    expect(promptIsAvailable('askable')).toBe(true);
  });

  /**
   * Not because she would mind being asked, but because there is nothing left to
   * ask *for*: the dialog is spent and the answer is yes.
   */
  it('is not available to a player who already said yes', () => {
    expect(promptIsAvailable('granted')).toBe(false);
  });

  /**
   * The one that makes this a rule rather than a boolean. iOS grants one system
   * dialog per install and two Android denials are permanent, so an explainer
   * here would end on a control that cannot do what it says.
   */
  it('is not available once the dialog has been spent', () => {
    expect(promptIsAvailable('spent')).toBe(false);
  });
});

describe('the second occasion: the first standby join', () => {
  it('explains at a join by a player who has not been asked this session', () => {
    expect(explainAtStandbyJoin({ standing: 'askable', askedThisSession: false })).toBe(true);
  });

  /**
   * `ADR-0061` says *the first* standby join. A player may join fifty queues,
   * and an ask repeated on each is furniture rather than an explanation.
   */
  it('does not explain at the second join of a session', () => {
    expect(explainAtStandbyJoin({ standing: 'askable', askedThisSession: true })).toBe(false);
  });

  /** Both halves are needed, so both are driven with the other held still. */
  it('does not explain to a player who already said yes, however many joins', () => {
    expect(explainAtStandbyJoin({ standing: 'granted', askedThisSession: false })).toBe(false);
  });

  it('does not explain once the dialog has been spent', () => {
    expect(explainAtStandbyJoin({ standing: 'spent', askedThisSession: false })).toBe(false);
  });
});
