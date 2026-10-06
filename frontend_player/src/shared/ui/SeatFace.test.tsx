/**
 * The face in a seat and the identifier under it — the drawing the group page, Fill in and a
 * booked game's players card share since it came below them (#574).
 *
 * What a screen can observe of it: an open seat draws what the court puts in it, a seated one draws
 * the face instead, and the caption under a face is three characters of the handle, hidden — the
 * seat's own spoken name carries the handle whole.
 */

import { render, screen } from '@testing-library/react-native';
import { Text } from 'react-native';

import { SEAT_NAME_LETTERS, SeatCaption, SeatFace, seatCaptionName } from './SeatFace';

const PLUS = 'plus';

describe('a face in a seat', () => {
  it('draws what the court puts in an open seat', () => {
    render(
      <SeatFace size={46} occupant={{ kind: 'empty' }} ring="empty">
        <Text>{PLUS}</Text>
      </SeatFace>,
    );

    expect(screen.getByText(PLUS)).toBeTruthy();
  });

  it('draws the face, and not what the court handed it, in a seat somebody is in', () => {
    render(
      <SeatFace size={46} occupant={{ kind: 'player', playerId: 'p-1' }} ring="seated">
        <Text>{PLUS}</Text>
      </SeatFace>,
    );

    expect(screen.queryByText(PLUS)).toBeNull();
  });
});

describe('the identifier under a face', () => {
  it('cuts the handle to three characters, hard, and marks nothing for the rest', () => {
    expect(seatCaptionName('tomek.p')).toBe('tom');
    expect(seatCaptionName('tomek.p')).toHaveLength(SEAT_NAME_LETTERS);
    expect(seatCaptionName('al')).toBe('al');
  });

  it('is drawn and never spoken — the seat says the whole handle', () => {
    render(<SeatCaption size={46} name="tomek.p" level={2.71} />);

    const drawn = screen.getByText('tom', { includeHiddenElements: true });
    expect(drawn.props.ellipsizeMode).toBe('clip');
    expect(screen.getByText('2,71', { includeHiddenElements: true })).toBeTruthy();
    expect(screen.queryByText('tom')).toBeNull();
    expect(screen.queryByText('tomek.p', { includeHiddenElements: true })).toBeNull();
  });
});
