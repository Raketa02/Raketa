/** How a refused share is confirmed on the phone (the mechanics §12.2). */

import { confirmsWith } from './seatCharge';

describe('confirmsWith', () => {
  it('pays a decline with another card, typed for it', () => {
    expect(confirmsWith({ refusal: 'DECLINED' })).toBe('typed');
  });

  it('asks the bank about the card on file for every other refusal', () => {
    expect(confirmsWith({ refusal: 'AUTHENTICATION_REQUIRED' })).toBe('onFile');
    expect(confirmsWith({ refusal: null })).toBe('onFile');
  });
});
