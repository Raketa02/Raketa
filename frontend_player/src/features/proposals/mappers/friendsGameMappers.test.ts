import {
  toFriendsGameAccepted,
  toFriendsGameSent,
  toSendFriendsGameRequest,
} from './friendsGameMappers';

describe('toSendFriendsGameRequest', () => {
  it('spells the card as it was read, the court it names and how to pay', () => {
    expect(
      toSendFriendsGameRequest({
        sport: 'padel',
        ask: { kind: 'forFun', friendIds: ['ewa', 'magda', 'ania'], partnerId: 'magda' },
        court: { courtId: 'court-3', startsAt: '2026-11-07T09:00:00Z' },
        payMode: 'WHOLE_COURT',
      }),
    ).toEqual({
      sport: 'PADEL',
      kind: 'FOR_FUN',
      friend_ids: ['ewa', 'magda', 'ania'],
      partner_id: 'magda',
      court_id: 'court-3',
      starts_at: '2026-11-07T09:00:00Z',
      pay_mode: 'WHOLE_COURT',
      booking_id: null,
    });
  });

  it('sends the evenest sides as no partner, and a send again under its booking', () => {
    expect(
      toSendFriendsGameRequest({
        sport: 'tennis',
        ask: { kind: 'competitive', friendIds: ['ania'] },
        court: { courtId: 'c', startsAt: 's' },
        payMode: 'SPLIT_THE_COST',
        bookingId: 'b-1',
      }),
    ).toMatchObject({ partner_id: null, booking_id: 'b-1', kind: 'COMPETITIVE' });
  });
});

describe('the answers', () => {
  it('reads a send booked, and one whose payments wait to be confirmed', () => {
    expect(
      toFriendsGameSent({
        booking_id: 'b-1',
        booked: { booking_id: 'b-1', game_id: 'g-1' },
        your_payments: [],
      }),
    ).toEqual({ bookingId: 'b-1', booked: true, yourPayments: [] });
    expect(
      toFriendsGameSent({
        booking_id: 'b-1',
        booked: null,
        your_payments: [
          {
            seat_charge_id: 'sc-1',
            refusal: 'AUTHENTICATION_REQUIRED',
            confirm_by: null,
            time_to: null,
          },
        ],
      }),
    ).toEqual({
      bookingId: 'b-1',
      booked: false,
      yourPayments: [{ seatChargeId: 'sc-1', refusal: 'AUTHENTICATION_REQUIRED' }],
    });
  });

  it('reads an accept, whole or not, and a share refused', () => {
    expect(
      toFriendsGameAccepted({ booking_id: 'b-1', accepted: true, whole: true, your_payment: null }),
    ).toEqual({ bookingId: 'b-1', accepted: true, whole: true });
    expect(
      toFriendsGameAccepted({
        booking_id: 'b-1',
        accepted: false,
        whole: false,
        your_payment: {
          seat_charge_id: 'sc-2',
          refusal: 'DECLINED',
          confirm_by: '2026-10-02T08:00:00Z',
          time_to: 'FIX_THE_CARD',
        },
      }),
    ).toEqual({
      bookingId: 'b-1',
      accepted: false,
      whole: false,
      yourPayment: {
        seatChargeId: 'sc-2',
        refusal: 'DECLINED',
        confirmBy: '2026-10-02T08:00:00Z',
        timeTo: 'FIX_THE_CARD',
      },
    });
  });
});
