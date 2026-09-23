import { selectedIn, useRadarView } from './radarView.store';

afterEach(() => useRadarView.getState().reset());

describe('where the radar was left', () => {
  it('opens at home — nothing kept, nobody selected', () => {
    expect(useRadarView.getState().view).toBeUndefined();
    expect(useRadarView.getState().selection).toBeUndefined();
  });

  it('keeps a view and a selection, and ◉ drops both', () => {
    useRadarView.getState().setView({ centre: { x: 2, y: -1 }, widthKm: 5.4 });
    useRadarView.getState().select({ sport: 'padel', playerId: 'marek' });
    expect(useRadarView.getState().view).toEqual({ centre: { x: 2, y: -1 }, widthKm: 5.4 });
    expect(useRadarView.getState().selection).toEqual({ sport: 'padel', playerId: 'marek' });

    useRadarView.getState().goHome();
    expect(useRadarView.getState().view).toBeUndefined();
    expect(useRadarView.getState().selection).toBeUndefined();
  });

  it('deselects without moving the view', () => {
    useRadarView.getState().setView({ centre: { x: 2, y: -1 }, widthKm: 5.4 });
    useRadarView.getState().select({ sport: 'padel', playerId: 'marek' });
    useRadarView.getState().deselect();
    expect(useRadarView.getState().view).toEqual({ centre: { x: 2, y: -1 }, widthKm: 5.4 });
    expect(useRadarView.getState().selection).toBeUndefined();
  });

  /** A sport switch clears the selection and keeps the view — by construction, not by an effect. */
  it('reads the selection for the sport it was made in and for no other', () => {
    const selection = { sport: 'padel', playerId: 'marek' } as const;
    expect(selectedIn(selection, 'padel')).toBe('marek');
    expect(selectedIn(selection, 'tennis')).toBeUndefined();
    expect(selectedIn(undefined, 'padel')).toBeUndefined();
    expect(selectedIn(selection, undefined)).toBeUndefined();
  });
});
