/**
 * What the row on You and the list behind the bell say (#559; mock 50): the choices that are on, in
 * the screen's order and the row's short names, and when a notice was given — and the bell's
 * number, drawn and spoken (#627; Q101).
 */

import {
  NOTIFICATIONS_COPY,
  bellFigure,
  bellSpoken,
  givenLine,
  noticeRowSpoken,
  notificationsRowLine,
} from './notificationsCopy';

describe('the row’s line', () => {
  it('names the choices that are on, short, in the screen’s order (mock 50)', () => {
    expect(notificationsRowLine(['youCompleteIt', 'challengesForYou', 'fillInAlerts'])).toBe(
      'You complete it · Challenges · Fill in alerts',
    );
    expect(notificationsRowLine(['fillInAlerts'])).toBe('Fill in alerts');
  });

  it('says only the seven always on are left when none is', () => {
    expect(notificationsRowLine([])).toBe(NOTIFICATIONS_COPY.noneChosen);
  });
});

describe('when a notice was given, on its row', () => {
  it('is the clock today', () => {
    expect(givenLine({ day: 'today', clock: '14:05' })).toBe('14:05');
  });

  it('is said yesterday', () => {
    expect(givenLine({ day: 'yesterday', clock: '22:00' })).toBe('Yesterday 22:00');
  });

  it('is the weekday within the week', () => {
    expect(givenLine({ day: 'weekday', weekday: 1, clock: '09:00' })).toBe('Mon 09:00');
    expect(givenLine({ day: 'weekday', weekday: 7, clock: '09:00' })).toBe('Sun 09:00');
  });

  it('is the date, day first, past it', () => {
    expect(givenLine({ day: 'date', date: '2026-09-20', clock: '09:00' })).toBe('20 Sep');
    expect(givenLine({ day: 'date', date: '2027-01-05', clock: '09:00' })).toBe('5 Jan');
  });
});

describe('the bell’s number (Q101)', () => {
  it('is nothing at nought', () => {
    expect(bellFigure(0)).toBeUndefined();
  });

  it('is the count up to 99', () => {
    expect(bellFigure(1)).toBe('1');
    expect(bellFigure(99)).toBe('99');
  });

  it('is 99+ above 99', () => {
    expect(bellFigure(100)).toBe('99+');
    expect(bellFigure(250)).toBe('99+');
  });

  it('is said on the bell’s name, exactly — a listener is not short of room', () => {
    expect(bellSpoken(0)).toBe(NOTIFICATIONS_COPY.bell);
    expect(bellSpoken(1)).toBe('Recent notifications, 1 new');
    expect(bellSpoken(250)).toBe('Recent notifications, 250 new');
  });
});

describe('a row of the list, spoken', () => {
  it('is the notice and when it was given', () => {
    expect(noticeRowSpoken('Someone left your game', 'Padel · Tue 19:00', '23:00', false)).toBe(
      'Someone left your game. Padel · Tue 19:00. 23:00',
    );
  });

  it('says first that it is new, on the visit it stands out', () => {
    expect(noticeRowSpoken('Someone left your game', 'Padel · Tue 19:00', '23:00', true)).toBe(
      'New. Someone left your game. Padel · Tue 19:00. 23:00',
    );
  });
});
