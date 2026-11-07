/** **A link, drawn** — the address a card prints, without the scheme the mocks never show. */

import { linkWithoutScheme } from './linkFormat';

describe('a link without its scheme', () => {
  it.each([
    ['https://raketa.app/join/K7PQ2MXA', 'raketa.app/join/K7PQ2MXA'],
    ['http://localhost:3001/f/tk4m9q2z', 'localhost:3001/f/tk4m9q2z'],
    ['raketa://f/tk4m9q2z', 'raketa://f/tk4m9q2z'],
  ])('draws %p as %p', (link, drawn) => {
    expect(linkWithoutScheme(link)).toBe(drawn);
  });
});
