/**
 * The door row's one rule that cannot be seen: **it is one element, spoken as its title and its
 * live line**, and it still says what it is while the line is not in.
 */

import { fireEvent, render, screen } from '@testing-library/react-native';

import { DoorRow, doorRowLabel } from './DoorRow';

describe('what a door row is called', () => {
  it('speaks the title and the live line together, as one element', () => {
    const onPress = jest.fn();
    render(<DoorRow glyph="calendar" title="Your week" line="10 slots ticked" onPress={onPress} />);

    const row = screen.getByRole('button', { name: 'Your week, 10 slots ticked' });
    fireEvent.press(row);

    expect(onPress).toHaveBeenCalledTimes(1);
    // The lead glyph and the chevron are decoration: nothing inside the row is its own element.
    expect(screen.getAllByRole('button')).toHaveLength(1);
  });

  it('is spoken as its title alone while the line is not in', () => {
    render(<DoorRow glyph="calendar" title="Your week" onPress={() => {}} />);

    expect(screen.getByRole('button', { name: 'Your week' })).toBeTruthy();
    expect(doorRowLabel('Your week', undefined)).toBe('Your week');
  });
});
