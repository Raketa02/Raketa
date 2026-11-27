/**
 * **Needs your answer, asked for by a link or a notice** (#817): Home laid down, and the kept Home's
 * sheet told — or, when no Home is there to hear it yet, the ask held for the one `openTab` mounts.
 */

import { openNeedsYourAnswer, whenNeedsYourAnswerAsked } from './needsYourAnswerAsked';
import { openTab } from './shellNavigation';

jest.mock('./shellNavigation', () => ({ openTab: jest.fn() }));

afterEach(() => jest.mocked(openTab).mockClear());

describe('openNeedsYourAnswer', () => {
  it('lays Home down from where the player is, and tells the Home that is there', () => {
    const heard = jest.fn();
    const stop = whenNeedsYourAnswerAsked(heard);

    openNeedsYourAnswer('/you');

    expect(openTab).toHaveBeenCalledWith('home', '/you');
    expect(heard).toHaveBeenCalledTimes(1);
    stop();
  });

  it('holds the ask for the Home that mounts after it — a stack that began elsewhere', () => {
    openNeedsYourAnswer('/you');

    const heard = jest.fn();
    const stop = whenNeedsYourAnswerAsked(heard);
    expect(heard).toHaveBeenCalledTimes(1);
    stop();

    // Taken once: the next Home to mount hears nothing.
    const later = jest.fn();
    const stopLater = whenNeedsYourAnswerAsked(later);
    expect(later).not.toHaveBeenCalled();
    stopLater();
  });

  it('leaves nothing held once a Home heard it', () => {
    const heard = jest.fn();
    const stop = whenNeedsYourAnswerAsked(heard);
    openNeedsYourAnswer('/');
    stop();

    const next = jest.fn();
    const stopNext = whenNeedsYourAnswerAsked(next);
    expect(next).not.toHaveBeenCalled();
    stopNext();
  });
});
