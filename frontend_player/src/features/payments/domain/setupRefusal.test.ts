import { AppError } from '@/shared/errors';

import { bankRefusal, setupRefusal } from './setupRefusal';

const refused = (code: string, status = 409) =>
  new AppError('conflict', 'business-conflict', 'refused', { code, status });

describe('what a refusal costs the checklist', () => {
  it('sends a declined card back to the card details', () => {
    expect(setupRefusal(refused('payment_method_declined'))).toEqual({ kind: 'CARD_DECLINED' });
  });

  it('keeps the bank step open while its check is not done', () => {
    expect(setupRefusal(refused('payment_setup_not_finished'))).toEqual({ kind: 'BANK_NOT_DONE' });
  });

  it('starts over when the setup is gone, or has no terms', () => {
    expect(setupRefusal(refused('payment_setup_not_started'))).toEqual({ kind: 'START_OVER' });
    expect(setupRefusal(refused('payment_terms_not_accepted'))).toEqual({ kind: 'START_OVER' });
  });

  it('stops at the terms when the words on this phone are old', () => {
    expect(setupRefusal(refused('payment_terms_outdated'))).toEqual({ kind: 'TERMS_OUTDATED' });
  });

  it('says anything else and moves nothing — on the code, never the status', () => {
    const exhausted = refused('payment_setups_exhausted', 429);
    expect(setupRefusal(exhausted)).toEqual({ kind: 'SAY_SO', error: exhausted });
    const otherConflict = refused('something_else');
    expect(setupRefusal(otherConflict)).toEqual({ kind: 'SAY_SO', error: otherConflict });
  });
});

describe("what the bank's refusal costs the checklist", () => {
  it('sends a declined card back to the card details, as the server’s decline does', () => {
    expect(bankRefusal('declined')).toEqual(setupRefusal(refused('payment_method_declined')));
  });

  it('keeps step 4 open when the check was closed, or the answer never came', () => {
    expect(bankRefusal('cancelled')).toEqual({ kind: 'BANK_CLOSED' });
    expect(bankRefusal('failed')).toEqual({ kind: 'BANK_FAILED' });
  });
});
