import { offlineMessage } from './offlineMessage';

describe('the offline sentence', () => {
  it('says a paused act will resume by itself', () => {
    expect(offlineMessage('resumes')).toBe(
      "You're offline. This will load as soon as you're back.",
    );
  });

  it('says an act set to fail rather than defer cannot be sent', () => {
    expect(offlineMessage('does-not-resume')).toBe(
      "You're offline. This can't be sent until you're back.",
    );
  });

  it('has exactly two values, split on resumption rather than on the HTTP verb', () => {
    // The line-up forecast is a `POST` that pauses, and it takes the first sentence. A split
    // on the verb would hand it the second one, which would be false of it.
    expect(new Set([offlineMessage('resumes'), offlineMessage('does-not-resume')]).size).toBe(2);
  });

  it('names no subject, because it is rendered beside the act it is about', () => {
    // The reason `OfflineBanner` is declined: the sentence sits at the paused thing rather
    // than over a screen, so "this" is the control the player is looking at.
    for (const resumption of ['resumes', 'does-not-resume'] as const) {
      expect(offlineMessage(resumption)).toMatch(/^You're offline\./);
    }
  });
});
