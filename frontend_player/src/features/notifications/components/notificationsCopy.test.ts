/**
 * What the row on You and the list behind the bell say (#559; mock 50): the choices that are on, in
 * the screen's order and the row's short names, and when a notice was given.
 */

import { NOTIFICATIONS_COPY, givenLine, notificationsRowLine } from './notificationsCopy';

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
