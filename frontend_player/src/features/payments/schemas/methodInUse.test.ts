import { methodInUseFrom } from './methodInUse';

describe("a removal's refusal, read", () => {
  it('names what still needs the method', () => {
    expect(methodInUseFrom({ live_yeses: 2, upcoming_games: 1 })).toEqual({
      liveYeses: 2,
      upcomingGames: 1,
    });
  });

  it('is no counts when the details are missing or not whole numbers', () => {
    expect(methodInUseFrom(undefined)).toBeNull();
    expect(methodInUseFrom({ live_yeses: '2', upcoming_games: 1 })).toBeNull();
    expect(methodInUseFrom({ live_yeses: -1, upcoming_games: 0 })).toBeNull();
    expect(methodInUseFrom({ live_yeses: 1.5, upcoming_games: 0 })).toBeNull();
  });
});
