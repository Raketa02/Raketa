/**
 * 10.3's header, on the two things [#401](https://github.com/Raketa02/Raketa/issues/401) added
 * to it: a **sub-line** under the title, and a spoken name that may differ from the drawn one.
 *
 * Asserted the way a listener meets it — by role and name — because the whole point of the second
 * addition is that what is drawn and what is spoken are two different strings, and only one of
 * them is the element's name.
 */

import { render, screen, within } from '@testing-library/react-native';

import { ScreenHeader } from './ScreenHeader';

describe('the title and its sub-line', () => {
  it('draws the sub-line under the title, inside the one element the title is', () => {
    render(<ScreenHeader title="tomek, ola" subline="Padel · planning" />);

    const header = screen.getByRole('header');

    expect(within(header).getByText('tomek, ola')).toBeTruthy();
    expect(within(header).getByText('Padel · planning')).toBeTruthy();
  });

  /** The eyebrow labels a region above; the sub-line qualifies the title below. Both may exist. */
  it('keeps the eyebrow above and outside the element the title is', () => {
    render(<ScreenHeader eyebrow="Play" title="Find a game" subline="one search" />);

    const header = screen.getByRole('header');

    expect(within(header).getByText('Find a game')).toBeTruthy();
    expect(within(header).queryByText('Play')).toBeNull();
    expect(screen.getByText('Play')).toBeTruthy();
  });

  /**
   * Named by its own words and **not labelled with them**: a header carrying its title as a label
   * would answer for it in every `getByLabelText` that means the control beside it — Play's
   * segment is called *Match me* under a header saying *Match me*.
   */
  it('is one element named by the title alone where there is no sub-line, with no label of its own', () => {
    render(<ScreenHeader title="Find a game" />);

    expect(screen.getByRole('header', { name: 'Find a game' })).toBeTruthy();
    expect(screen.queryByLabelText('Find a game')).toBeNull();
  });
});

describe('what the header is called', () => {
  /**
   * §20.4: *the visible label truncates, the spoken one never does*. The conversation draws the
   * handles' stems and speaks them whole, and this is the slot that lets it.
   */
  it('takes a spoken name that differs from the drawn line, and speaks only that', () => {
    render(
      <ScreenHeader
        title="tomek, ola"
        subline="Padel · planning"
        titleLabel="tomek.p and ola.k, Padel, planning"
      />,
    );

    const header = screen.getByRole('header', { name: 'tomek.p and ola.k, Padel, planning' });

    expect(within(header).getByText('tomek, ola')).toBeTruthy();
    expect(within(header).getByText('Padel · planning')).toBeTruthy();
    // The name is the label and only the label: what a listener hears, not what is drawn — so
    // it is found the way every other named thing in this app is, and the drawn line is not.
    expect(screen.getByLabelText('tomek.p and ola.k, Padel, planning')).toBe(header);
    expect(screen.queryByLabelText('tomek, ola')).toBeNull();
  });
});
