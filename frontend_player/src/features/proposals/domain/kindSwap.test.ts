import type { DeckSegment } from './deck';
import {
  buttonsMotion,
  kindDrawn,
  stackMotion,
  swapTo,
  takesAnswers,
  type KindSwap,
} from './kindSwap';

const BOTH: readonly DeckSegment[] = [
  { kind: 'competitive', count: 5 },
  { kind: 'forFun', count: 1 },
];

/** Competitive dealing nothing — For fun's one card the only one. */
const FUN_ONLY_DEALS: readonly DeckSegment[] = [
  { kind: 'competitive', count: 0 },
  { kind: 'forFun', count: 1 },
];

const fromCards = { from: 'competitive', stack: 'cards', held: true, kinds: BOTH } as const;

describe('a pick from the Games tab’s menu begins a swap (#863)', () => {
  it('draws the kind it leaves while the stack goes out, then the kind picked', () => {
    const swap = swapTo(undefined, fromCards, 'forFun');

    expect(swap.phase).toBe('out');
    expect(kindDrawn(swap, 'forFun')).toBe('competitive');
    expect(kindDrawn({ ...swap, phase: 'in' }, 'forFun')).toBe('forFun');
    expect(kindDrawn(undefined, 'forFun')).toBe('forFun');
  });

  it('keeps the buttons when the kind left dealt a card and the kind picked counts one', () => {
    expect(swapTo(undefined, fromCards, 'forFun')).toMatchObject({ held: true, promised: true });
    expect(
      swapTo(undefined, { ...fromCards, from: 'forFun', kinds: FUN_ONLY_DEALS }, 'competitive'),
    ).toMatchObject({ held: true, promised: false });
    // Its count is the menu's — no read of the kind picked is waited for.
    expect(swapTo(undefined, { ...fromCards, kinds: undefined }, 'forFun').promised).toBe(false);
  });

  it('only changes where it lands when the stack is still going out — its clock runs on', () => {
    const going = swapTo(undefined, { ...fromCards, kinds: FUN_ONLY_DEALS }, 'forFun');
    const back = swapTo(
      going,
      { from: 'forFun', stack: 'cards', held: false, kinds: FUN_ONLY_DEALS },
      'competitive',
    );

    expect(back).toEqual({ from: 'competitive', phase: 'out', held: true, promised: false });
  });

  it('begins again from what is drawn once the other kind is coming in', () => {
    const coming: KindSwap = { from: 'competitive', phase: 'in', held: true, promised: true };

    expect(
      swapTo(coming, { from: 'forFun', stack: 'nothing', held: false, kinds: BOTH }, 'competitive'),
    ).toEqual({
      from: 'forFun',
      phase: 'out',
      held: false,
      promised: true,
    });
  });

  it('comes straight in from a read on its way, which has no stack to send out', () => {
    const coming: KindSwap = { from: 'competitive', phase: 'in', held: true, promised: true };

    expect(
      swapTo(coming, { from: 'forFun', stack: 'reading', held: true, kinds: BOTH }, 'competitive'),
    ).toEqual({ from: 'forFun', phase: 'in', held: true, promised: true });
  });
});

describe('the stack’s motion', () => {
  const swap: KindSwap = { from: 'competitive', phase: 'out', held: true, promised: true };

  it('stands at rest with no swap', () => {
    expect(stackMotion(undefined, true)).toBe('rest');
    expect(stackMotion(undefined, false)).toBe('rest');
  });

  it('goes out, then comes in once the kind picked is read — and is away until it is', () => {
    expect(stackMotion(swap, true)).toBe('out');
    expect(stackMotion({ ...swap, phase: 'in' }, false)).toBe('away');
    expect(stackMotion({ ...swap, phase: 'in' }, true)).toBe('in');
  });

  it('takes no answer until the stack it brings has landed', () => {
    expect(takesAnswers(swap)).toBe(false);
    expect(takesAnswers({ ...swap, phase: 'in' })).toBe(false);
    expect(takesAnswers(undefined)).toBe(true);
  });
});

describe('the buttons on the swap', () => {
  const out = (held: boolean, promised: boolean): KindSwap => ({
    from: 'competitive',
    phase: 'out',
    held,
    promised,
  });
  const coming = (held: boolean, promised: boolean): KindSwap => ({
    ...out(held, promised),
    phase: 'in',
  });

  it('are drawn under cards and nowhere else when nothing is swapping', () => {
    expect(buttonsMotion(undefined, 'cards')).toBe('kept');
    expect(buttonsMotion(undefined, 'nothing')).toBe('none');
    expect(buttonsMotion(undefined, 'reading')).toBe('none');
  });

  it('stay when both kinds deal cards — under the skeleton too', () => {
    expect(buttonsMotion(out(true, true), 'cards')).toBe('kept');
    expect(buttonsMotion(coming(true, true), 'reading')).toBe('kept');
    expect(buttonsMotion(coming(true, true), 'cards')).toBe('kept');
  });

  it('fade out with the stack when the kind picked deals nothing, and the starting card has none', () => {
    expect(buttonsMotion(out(true, false), 'cards')).toBe('out');
    expect(buttonsMotion(coming(true, false), 'reading')).toBe('none');
    expect(buttonsMotion(coming(true, false), 'nothing')).toBe('none');
  });

  it('fade back in from the starting card to a kind with cards', () => {
    expect(buttonsMotion(out(false, true), 'nothing')).toBe('none');
    expect(buttonsMotion(coming(false, true), 'reading')).toBe('none');
    expect(buttonsMotion(coming(false, true), 'cards')).toBe('in');
  });

  it('fade in where the count said nothing and the read dealt a card — and go where it said one and dealt none', () => {
    expect(buttonsMotion(coming(true, false), 'cards')).toBe('in');
    expect(buttonsMotion(coming(true, true), 'nothing')).toBe('none');
  });
});
