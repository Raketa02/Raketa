import { parseRankingsParams } from './routeParams';

describe('the Rankings route’s params', () => {
  it('reads the sport the page was opened on', () => {
    expect(parseRankingsParams({ sport: 'squash' })).toEqual({ sport: 'squash' });
  });

  it('reads no sport from none, from a sport this build does not know, or from a list', () => {
    // An address is untrusted: anything but one sport opens the page as the trophy with no sport
    // would — on the deck's last sport, or padel.
    expect(parseRankingsParams({})).toEqual({});
    expect(parseRankingsParams({ sport: 'curling' })).toEqual({});
    expect(parseRankingsParams({ sport: ['padel', 'tennis'] })).toEqual({});
  });
});
