'use client';

import { Button } from '@/ui/Button';
import tableStyles from '@/ui/Table.module.css';
import { Tag } from '@/ui/Tag';

import { BOOKINGS_COPY, knownZloty, sportAndKind } from '../copy';
import type { Booking, BookingStatus, PaymentDue } from '../mappers';

import { askedAbout, type Asked, type AskedToCancel } from './Asked';
import styles from './Bookings.module.css';
import { RequestActions } from './RequestActions';
import { useReadAgainAt } from './useReadAgainAt';

const COPY = BOOKINGS_COPY;

const TONES = {
  WAITING_FOR_YOU: 'amber',
  WAITING_FOR_A_PAYMENT: 'amber',
  BOOKED: 'green',
  SEAT_OPEN: 'amber',
  CALLED_OFF: 'red',
  PLAYED: 'neutral',
} as const satisfies Record<BookingStatus, string>;

/** The id a booking's row carries, so a link can point at it. */
export function rowId(bookingId: string): string {
  return `booking-${bookingId}`;
}

/**
 * Until when the club's yes waits on one player's card or payment, never whose. Once that time
 * comes the page is read again, and the game reads booked or called off.
 */
function PaymentAwaited({ due }: { due: PaymentDue }) {
  useReadAgainAt(due);
  return <span className={styles.why}>{COPY.waitingFor[due.timeTo](due.until)}</span>;
}

function Status({ booking }: { booking: Booking }) {
  const { calledOff, paymentDue } = booking;
  return (
    <div className={styles.status}>
      <Tag tone={TONES[booking.status]}>{COPY.statuses[booking.status]}</Tag>
      {paymentDue === null ? null : <PaymentAwaited due={paymentDue} />}
      {calledOff === null ? null : (
        <span className={styles.why}>
          {COPY.calledOff[calledOff.reason]}
          {calledOff.cancel === null ? null : ` · ${COPY.cancelReasons[calledOff.cancel]}`}
        </span>
      )}
    </div>
  );
}

function Players({ booking }: { booking: Booking }) {
  return (
    <ul className={styles.players}>
      {booking.players.map((player) => (
        <li key={player.id}>
          <span className={styles.player}>{player.name ?? COPY.nameless}</span>
          {player.share !== null || player.checkedIn ? (
            <span className={styles.marks}>
              {player.share === null ? null : (
                <span data-share={player.share}>{` ${COPY.shares[player.share]}`}</span>
              )}
              {player.checkedIn ? ` ${COPY.checkedIn}` : null}
            </span>
          ) : null}
        </li>
      ))}
      {Array.from({ length: booking.openSeats }, (_, seat) => (
        <li key={`open-${seat}`} className={styles.open}>
          {COPY.openSeat}
        </li>
      ))}
    </ul>
  );
}

function Money({ booking }: { booking: Booking }) {
  const { money } = booking;
  const lines = [
    [COPY.money.price, money.priceGrosze],
    [COPY.money.collected, money.collectedGrosze],
    [COPY.money.refunded, money.refundedGrosze],
  ] as const;
  return (
    <dl className={styles.money}>
      {lines.map(([label, grosze]) => (
        <div key={label} className={styles.moneyLine}>
          <dt>{label}</dt> <dd data-unknown={grosze === null}>{knownZloty(grosze)}</dd>
        </div>
      ))}
    </dl>
  );
}

function From({ booking }: { booking: Booking }) {
  const { from } = booking;
  if (from === null) return <span className={styles.gone}>{COPY.from.gone}</span>;
  return (
    <div className={styles.from}>
      <span className={styles.group}>{from.name}</span>{' '}
      <span className={styles.groupKind}>
        {from.official ? COPY.from.official : COPY.from.player}
      </span>
    </div>
  );
}

/**
 * **One day's bookings** (the screens B4): each game's hour and court, sport and kind, its
 * players (their share *held* or *taken*, *checked in ✓*), its status (with until when a yes
 * waits on one player's card or payment), its money and the group it came from, and what the
 * club may do about it: answer a request before its countdown ends, or move or cancel a game
 * until it starts. Every act waits while one is under way. The booking a link pointed at is
 * marked.
 */
export function BookingsTable({
  bookings,
  pointedAt,
  action,
  pending,
  onRefuse,
  onMove,
  onCancel,
}: {
  bookings: readonly Booking[];
  /** The booking a link pointed at, or `null`. */
  pointedAt: string | null;
  action: (form: FormData) => void;
  pending: boolean;
  onRefuse: (game: Asked) => void;
  onMove: (game: Asked) => void;
  onCancel: (game: AskedToCancel) => void;
}) {
  return (
    <table className={tableStyles.table}>
      <thead className={tableStyles.head}>
        <tr>
          <th scope="col">{COPY.columns.when}</th>
          <th scope="col">{COPY.columns.sport}</th>
          <th scope="col">{COPY.columns.players}</th>
          <th scope="col">{COPY.columns.status}</th>
          <th scope="col">{COPY.columns.money}</th>
          <th scope="col">{COPY.columns.from}</th>
          <th scope="col">
            <span className="visually-hidden">{COPY.columns.actions}</span>
          </th>
        </tr>
      </thead>
      <tbody>
        {bookings.map((booking) => {
          const game = askedAbout(booking);
          return (
            <tr
              key={booking.id}
              id={rowId(booking.id)}
              className={styles.row}
              aria-current={booking.id === pointedAt ? 'true' : undefined}
            >
              <th scope="row" className={styles.when}>
                <span className={styles.hours}>
                  {booking.hour.from}–{booking.hour.until}
                </span>{' '}
                <span className={styles.court}>{booking.court}</span>
              </th>
              <td>{sportAndKind(booking.sport, booking.kind)}</td>
              <td>
                <Players booking={booking} />
              </td>
              <td>
                <Status booking={booking} />
              </td>
              <td>
                <Money booking={booking} />
              </td>
              <td>
                <From booking={booking} />
              </td>
              <td>
                {booking.status === 'WAITING_FOR_YOU' && booking.answerBy !== null ? (
                  <RequestActions
                    id={booking.id}
                    name={game.name}
                    answerBy={booking.answerBy}
                    action={action}
                    pending={pending}
                    onRefuse={() => onRefuse(game)}
                  />
                ) : booking.mayMoveOrCancel ? (
                  <div className={styles.actions}>
                    <Button
                      type="button"
                      tone="secondary"
                      disabled={pending}
                      onClick={() => onMove(game)}
                      aria-label={`${COPY.move} ${game.name}`}
                    >
                      {COPY.move}
                    </Button>
                    <Button
                      type="button"
                      tone="danger"
                      disabled={pending}
                      onClick={() => onCancel({ ...game, givesBack: booking.cancelGivesBack })}
                      aria-label={`${COPY.cancel} ${game.name}`}
                    >
                      {COPY.cancel}
                    </Button>
                  </div>
                ) : null}
              </td>
            </tr>
          );
        })}
      </tbody>
    </table>
  );
}
