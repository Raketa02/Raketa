import {
  ALL_CLOSED,
  FOR_YOU_LINES,
  foldRan,
  forYouShown,
  lineToStartOn,
  pressLine,
  settleLine,
  type ForYouLine,
  type OpenLine,
} from './forYou';

const everyLine = (): Readonly<Record<ForYouLine, boolean>> => ({
  hottestGroups: true,
  sameLevel: true,
  newInRaketa: true,
  sameVibe: true,
  topTen: true,
});

const shownBut = (...hidden: ForYouLine[]) => {
  const shown = { ...everyLine() };
  for (const line of hidden) shown[line] = false;
  return shown;
};

const FOLDS = { folds: true } as const;
const open = (line: ForYouLine, pressed = true): OpenLine => ({
  chosen: line,
  drawn: line,
  folding: false,
  pressed,
});

describe('FOR YOU’s five lines', () => {
  /** ADR-0205 §5's table: the old rows' order, under their new titles. */
  it('stand in the rows’ order', () => {
    expect(FOR_YOU_LINES).toEqual([
      'hottestGroups',
      'sameLevel',
      'newInRaketa',
      'sameVibe',
      'topTen',
    ]);
  });

  it('are all closed at the start, and nothing has been chosen', () => {
    expect(ALL_CLOSED).toEqual({ chosen: undefined, drawn: null, folding: false, pressed: false });
  });

  /** Q21: with all five hidden, FOR YOU goes too. */
  it('are shown as a section while any one of them is', () => {
    expect(forYouShown(everyLine())).toBe(true);
    expect(forYouShown(shownBut('hottestGroups', 'sameLevel', 'newInRaketa', 'sameVibe'))).toBe(
      true,
    );
    expect(forYouShown(shownBut(...FOR_YOU_LINES))).toBe(false);
  });

  /** Q38: joining a group is a groupless player's next step. */
  it('start on Groups heating up for a player in no group, and on none for anybody else', () => {
    expect(lineToStartOn({ inNoGroup: true })).toBe('hottestGroups');
    expect(lineToStartOn({ inNoGroup: false })).toBeUndefined();
  });
});

describe('a press on a line’s header', () => {
  it('opens a line at once when none is open', () => {
    expect(pressLine(ALL_CLOSED, 'sameLevel', FOLDS)).toEqual(open('sameLevel'));
  });

  it('closes the open line, which folds', () => {
    expect(pressLine(open('sameLevel'), 'sameLevel', FOLDS)).toEqual({
      chosen: null,
      drawn: null,
      folding: true,
      pressed: true,
    });
  });

  /** Q10 and the brief: one line at a time — the first folds, then the second unfolds. */
  it('on another line folds the open one first, the second chosen and not yet drawn', () => {
    expect(pressLine(open('sameLevel'), 'topTen', FOLDS)).toEqual({
      chosen: 'topTen',
      drawn: null,
      folding: true,
      pressed: true,
    });
  });

  /** The two never run at once: whatever is pressed while a line folds waits for the fold. */
  it('while a line folds, chooses the line pressed and waits — never unfolding beside the fold', () => {
    const switching = pressLine(open('sameLevel'), 'sameVibe', FOLDS);
    expect(pressLine(switching, 'topTen', FOLDS)).toEqual({
      chosen: 'topTen',
      drawn: null,
      folding: true,
      pressed: true,
    });

    const closing = pressLine(open('sameLevel'), 'sameLevel', FOLDS);
    expect(pressLine(closing, 'newInRaketa', FOLDS)).toEqual({
      chosen: 'newInRaketa',
      drawn: null,
      folding: true,
      pressed: true,
    });
  });

  it('keeps waiting when the line already waiting is pressed again', () => {
    const switching = pressLine(open('sameLevel'), 'topTen', FOLDS);

    expect(pressLine(switching, 'topTen', FOLDS)).toBe(switching);
  });

  /** ADR-0205 §8: under Reduce motion, everything is instant. */
  it('switches and closes at once when nothing folds', () => {
    expect(pressLine(open('sameLevel'), 'topTen', { folds: false })).toEqual(open('topTen'));
    expect(pressLine(open('sameLevel'), 'sameLevel', { folds: false })).toEqual({
      chosen: null,
      drawn: null,
      folding: false,
      pressed: true,
    });
  });
});

describe('once the fold has run', () => {
  it('draws the line chosen while it ran', () => {
    const switching = pressLine(open('sameLevel'), 'topTen', FOLDS);

    expect(foldRan(switching)).toEqual(open('topTen'));
  });

  it('draws nothing after a close, the fold over', () => {
    const closing = pressLine(open('sameLevel'), 'sameLevel', FOLDS);

    expect(foldRan(closing)).toEqual({ chosen: null, drawn: null, folding: false, pressed: true });
  });

  it('changes nothing when nothing was folding', () => {
    const drawn = open('topTen');
    expect(foldRan(drawn)).toBe(drawn);
    expect(foldRan(ALL_CLOSED)).toBe(ALL_CLOSED);
  });
});

describe('what is shown settles the open line', () => {
  it('changes nothing while the open line is shown', () => {
    const now = open('newInRaketa');

    expect(settleLine(now, everyLine(), undefined)).toBe(now);
  });

  /** Q21: a line that empties while open closes and goes — and stays closed if it comes back. */
  it('closes a line that is no longer shown', () => {
    expect(settleLine(open('hottestGroups'), shownBut('hottestGroups'), undefined)).toEqual({
      chosen: null,
      drawn: null,
      folding: false,
      pressed: true,
    });
  });

  it('forgets a line chosen while the fold ran, once it is no longer shown', () => {
    const switching = pressLine(open('sameLevel'), 'topTen', FOLDS);

    expect(settleLine(switching, shownBut('topTen'), undefined)).toEqual({
      chosen: null,
      drawn: null,
      folding: true,
      pressed: true,
    });
  });

  /** Q38: for a player in no group, Groups heating up starts open — opened by nobody's press. */
  it('opens the line a page starts on, once it is shown and nothing was chosen', () => {
    expect(settleLine(ALL_CLOSED, shownBut('hottestGroups'), 'hottestGroups')).toBe(ALL_CLOSED);
    expect(settleLine(ALL_CLOSED, everyLine(), 'hottestGroups')).toEqual(
      open('hottestGroups', false),
    );
  });

  it('never opens it over the reader’s own choice — a close included', () => {
    const closed = pressLine(open('hottestGroups'), 'hottestGroups', FOLDS);
    expect(settleLine(closed, everyLine(), 'hottestGroups')).toBe(closed);

    const other = open('topTen');
    expect(settleLine(other, everyLine(), 'hottestGroups')).toBe(other);
  });
});
