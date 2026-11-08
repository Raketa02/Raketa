/**
 * The two things about the switch a screen cannot observe, and one of them was a shipped bug.
 *
 * The role, the state and the label are asserted where a player meets them. What is here is
 * the **drawing** — the declared exception `ConfidenceRing.test.tsx` and `CourtPoster.test.tsx`
 * both take: the knob's position and the knob's value are the whole of what tells somebody
 * which way this control is set, and neither has a role, a name or any text under it.
 *
 * The prototype drew a white knob at both ends of the travel, and against its unchecked
 * `line` track that is 1,2:1 — the moving part invisible in half of its states. A suite that
 * only went through a screen would pass on that for ever.
 */

import { render, screen, userEvent } from '@testing-library/react-native';
import { StyleSheet, View, type TextStyle, type ViewStyle } from 'react-native';

import { composite, contrast, parse } from '@/test-support/contrast';

import { Switch } from './Switch';
import { theme } from './theme';

const flatten = (style: unknown) => StyleSheet.flatten(style as ViewStyle);
const inkOf = (style: unknown) => StyleSheet.flatten(style as TextStyle)?.color;

/** The track and the knob, in that order — the only two Views the control draws. */
function parts() {
  const drawn = screen.UNSAFE_queryAllByType(View).map((node) => flatten(node.props.style));
  const track = drawn.find((style) => style?.width === theme.size.switch.track);
  const knob = drawn.find((style) => style?.width === theme.size.switch.knob);
  return { track, knob };
}

function renderSwitch(checked: boolean, { onDark = false } = {}) {
  render(
    <Switch label="Swap players" checked={checked} onChange={() => undefined} onDark={onDark} />,
  );
  return parts();
}

describe('which way it is set', () => {
  it('is carried by the knob moving, before it is carried by anything else', () => {
    const off = renderSwitch(false).knob;
    screen.unmount();
    const on = renderSwitch(true).knob;

    // A shape, which is what Part 13 asks for — the two fills are allowed to be a fill
    // inversion only because the position has already said it.
    expect(off?.transform).not.toEqual(on?.transform);
  });

  it('travels the width of the track less the knob and its two insets', () => {
    const inset = (theme.size.switch.height - theme.size.switch.knob) / 2;
    const travel = theme.size.switch.track - theme.size.switch.knob - inset * 2;

    expect(renderSwitch(true).knob?.transform).toEqual([{ translateX: travel }]);
  });
});

describe('the knob', () => {
  /**
   * Not a taste decision and not a second on-colour: `surface` on `line` is 1,30:1, which is
   * the prototype's unchecked state and a control whose only moving part is not there.
   */
  it('takes the value that reads on the bed it is standing on, at both ends', () => {
    const off = renderSwitch(false);
    screen.unmount();
    const on = renderSwitch(true);

    expect(off.track?.backgroundColor).toBe(theme.color.line2);
    expect(off.knob?.backgroundColor).toBe(theme.color.night);
    expect(on.track?.backgroundColor).toBe(theme.color.ink);
    expect(on.knob?.backgroundColor).toBe(theme.color.surface);
  });
});

/**
 * **On the dark card** (#778, the hidden card on Rankings): 5.2's repaint read as a control. The
 * inversion read from the other side — off a quiet track under a light knob, on the track standing
 * out of its ground under a dark one.
 */
describe('on the dark card', () => {
  it('takes the dark ground’s values, at both ends', () => {
    const off = renderSwitch(false, { onDark: true });
    screen.unmount();
    const on = renderSwitch(true, { onDark: true });

    expect(off.track?.backgroundColor).toBe(theme.color.onDarkFill);
    expect(off.knob?.backgroundColor).toBe(theme.color.surface);
    expect(on.track?.backgroundColor).toBe(theme.color.surface);
    expect(on.knob?.backgroundColor).toBe(theme.color.night);
  });

  it('draws its words in the dark card’s two inks', () => {
    render(
      <Switch
        onDark
        label="Hidden from General"
        description="A line under it."
        checked={false}
        onChange={() => undefined}
      />,
    );

    expect(inkOf(screen.getByText('Hidden from General').props.style)).toBe(theme.color.surface);
    expect(inkOf(screen.getByText('A line under it.').props.style)).toBe(theme.color.onDarkTiny);
  });
});

/**
 * **In a card of door rows** (#778, *Show me in General* on You): the door row's lead, title and
 * line, and its divider from the second row on — so the switch's title starts where every title
 * above it does.
 */
describe('in a card of door rows', () => {
  it('draws the door row’s lead square and title', () => {
    render(
      <Switch
        door={{ glyph: 'eye', divided: false }}
        label="Show me in General"
        checked
        onChange={() => undefined}
      />,
    );

    const lead = screen
      .UNSAFE_queryAllByType(View)
      .map((node) => flatten(node.props.style))
      .find((style) => style?.width === theme.size.rowLead);
    expect(lead?.backgroundColor).toBe(theme.color.paper2);
    expect(flatten(screen.getByText('Show me in General').props.style)).toEqual(
      expect.objectContaining(theme.type.cardTitle),
    );
  });

  it('is divided from the row above it, as a door row is', () => {
    render(
      <Switch
        door={{ glyph: 'eye', divided: true }}
        label="Show me in General"
        checked
        onChange={() => undefined}
      />,
    );

    expect(flatten(screen.getByRole('switch').props.style)).toEqual(
      expect.objectContaining({ borderTopWidth: 1, borderTopColor: theme.color.line2 }),
    );
  });
});

describe('the control', () => {
  it('is the row, so the words are part of the target rather than beside it', () => {
    render(
      <Switch
        label="Swap players"
        description="Tap two seats to trade places."
        checked={false}
        onChange={() => undefined}
      />,
    );

    const row = flatten(screen.getByRole('switch').props.style);
    expect(row?.minHeight).toBe(theme.size.minTouch);
  });

  it('is named for the mode where the words drawn are what the mode being off means', () => {
    // The hidden card: *Hidden from General* drawn, and the switch is *Show me in General*, off.
    render(
      <Switch
        onDark
        label="Hidden from General"
        accessibilityLabel="Show me in General"
        checked={false}
        onChange={() => undefined}
      />,
    );

    expect(screen.getByRole('switch', { name: 'Show me in General' })).toBeTruthy();
    expect(screen.getByText('Hidden from General')).toBeTruthy();
  });

  it('announces the label alone, so the mode line is not read as part of the name', async () => {
    const onChange = jest.fn();
    render(
      <Switch
        label="Swap players"
        description="Off · tap a seat to swap that player for somebody else."
        checked={false}
        onChange={onChange}
      />,
    );

    const control = screen.getByRole('switch', { name: 'Swap players' });
    expect(control.props.accessibilityState).toEqual(expect.objectContaining({ checked: false }));

    await userEvent.press(control);
    expect(onChange).toHaveBeenCalledWith(true);
  });
});

/**
 * The three ratios 6.12 publishes, **derived rather than typed** — the rule
 * `textOnMedia.test.ts` and `posterHues.test.ts` already hold the court's four and the
 * poster's two to. A published number nothing derives is the two documents drifting.
 */
describe('what the knob is worth against its track', () => {
  /** WCAG 1.4.11: a graphical object needs 3:1 against what is adjacent to it. */
  const GRAPHICAL = 3;

  const ratio = (a: string, b: string) => contrast(parse(a).rgb, parse(b).rgb);

  it('clears 3:1 at both ends of the travel', () => {
    expect(ratio(theme.color.night, theme.color.line2)).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(ratio(theme.color.surface, theme.color.ink)).toBeGreaterThanOrEqual(GRAPHICAL);
  });

  it('is the two figures 6.12 prints', () => {
    expect(ratio(theme.color.night, theme.color.line2)).toBe(11.36);
    expect(ratio(theme.color.surface, theme.color.ink)).toBe(17.5);
  });

  it('clears it on the dark card too, at both ends — the two figures 6.12 prints for it', () => {
    // The off track is white at its alpha over `night`, so the knob is measured against that.
    const fill = parse(theme.color.onDarkFill);
    const offTrack = composite(fill.rgb, fill.alpha, parse(theme.color.night).rgb);
    const offKnob = contrast(parse(theme.color.surface).rgb, offTrack);
    const onKnob = ratio(theme.color.night, theme.color.surface);

    expect(offKnob).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(onKnob).toBeGreaterThanOrEqual(GRAPHICAL);
    expect(offKnob).toBe(7.88);
    expect(onKnob).toBe(13.29);
  });

  it('would not, on the white-at-both-ends the prototype drew', () => {
    // 6.12 prints this as the reason the knob takes two values. Pinned so the sentence keeps
    // its evidence when somebody reaches for one colour again.
    expect(ratio(theme.color.surface, theme.color.line)).toBe(1.3);
  });
});
