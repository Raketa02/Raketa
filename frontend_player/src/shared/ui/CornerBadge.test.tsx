/**
 * The segment's count mark, at its own seam — what it draws and that it says nothing itself: the
 * count belongs in the name of what it counts (a segment's, a group header's), never read twice.
 */

import { render, screen } from '@testing-library/react-native';
import { StyleSheet, type ViewStyle } from 'react-native';

import { CornerBadge } from './CornerBadge';
import { theme } from './theme';

describe('the corner badge', () => {
  it('draws the count in the Chats badge’s fill, at the segment’s size', () => {
    render(<CornerBadge count={2} />);

    const figure = screen.getByText('2', { includeHiddenElements: true });
    const badge = StyleSheet.flatten(figure.parent?.parent?.props.style as ViewStyle);
    expect(badge.backgroundColor).toBe(theme.color.coralInk);
    expect(badge.height).toBe(theme.size.segmentBadge);
    expect(badge.position).toBe('absolute');
  });

  it('says nothing to a screen reader', () => {
    render(<CornerBadge count={2} />);

    expect(screen.queryByText('2')).toBeNull();
  });
});
