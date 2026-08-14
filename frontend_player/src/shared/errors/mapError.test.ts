/**
 * Error mapping is pure and needs no renderer, so it is tested hardest.
 *
 * The assertions that matter are about *recovery*, not about kind: recovery is what a
 * screen and the session machine branch on, and getting it wrong is how a 403 signs
 * someone out or a mistyped password ends a session.
 */

import { mapDecodeFailure, mapErrorResponse, mapTransportFailure } from './mapError';

const envelope = (code: string, message = 'diagnostic') => ({
  code,
  message,
  trace_id: 'trace-abc',
  details: null,
});

describe('mapErrorResponse', () => {
  it('carries the code, trace id and status through', () => {
    const error = mapErrorResponse(409, envelope('question_not_outstanding'));

    expect(error.code).toBe('question_not_outstanding');
    expect(error.traceId).toBe('trace-abc');
    expect(error.status).toBe(409);
  });

  it('branches on the code, so two 409s from one endpoint family differ', () => {
    // The pair that motivated per-error codes: a double-tapped confirm versus the same
    // assessment resumed on a second device. Same status, opposite recoveries.
    const stale = mapErrorResponse(409, envelope('question_not_outstanding'));
    const finished = mapErrorResponse(409, envelope('assessment_already_finished'));

    expect(stale.code).not.toBe(finished.code);
  });

  it('never reads the message — copy can change without changing behaviour', () => {
    const original = mapErrorResponse(401, envelope('invalid_credentials', 'Bad login'));
    const reworded = mapErrorResponse(
      401,
      envelope('invalid_credentials', 'That email and password do not match'),
    );

    expect(reworded.recovery).toBe(original.recovery);
    expect(reworded.kind).toBe(original.kind);
  });

  describe('the session boundary', () => {
    it('does not sign the player out on a 403', () => {
      const error = mapErrorResponse(403, envelope('forbidden'));

      expect(error.invalidatesSession).toBe(false);
      expect(error.recovery).toBe('terminal');
    });

    it('does not sign the player out on a mistyped password', () => {
      // A 401 by status, but it answers a sign-in attempt: there is no session to end,
      // and the recovery is to retype something.
      const error = mapErrorResponse(401, envelope('invalid_credentials'));

      expect(error.invalidatesSession).toBe(false);
      expect(error.recovery).toBe('requires-user-correction');
    });

    it('does not sign the player out on a disabled account', () => {
      const error = mapErrorResponse(401, envelope('account_disabled'));

      expect(error.invalidatesSession).toBe(false);
    });

    it.each([
      'access_token_expired',
      'access_token_invalid',
      'access_token_missing',
      'access_token_subject_malformed',
      'refresh_token_expired',
      'refresh_token_revoked',
      'refresh_token_not_recognised',
      'refresh_token_mismatch',
      'invalid_refresh_token',
    ])('ends the session on %s', (code) => {
      expect(mapErrorResponse(401, envelope(code)).invalidatesSession).toBe(true);
    });

    it('ends the session on a 401 whose code this build has never seen', () => {
      // Old builds live on real phones for months. A new 401 code must still be
      // recognised as an authentication failure rather than falling through as unknown.
      const error = mapErrorResponse(401, envelope('token_bound_to_retired_device'));

      expect(error.invalidatesSession).toBe(true);
    });
  });

  describe('recovery by status, for codes this build does not know', () => {
    it.each([
      [400, 'requires-user-correction'],
      [404, 'terminal'],
      [409, 'business-conflict'],
      [422, 'requires-user-correction'],
      [429, 'retryable-by-user'],
      [500, 'retryable-automatically'],
      [503, 'retryable-automatically'],
    ])('maps %i to %s', (status, recovery) => {
      expect(mapErrorResponse(status, envelope('something_new')).recovery).toBe(recovery);
    });
  });

  it('treats a signup conflict as a correction, not a reconcile', () => {
    // 409 by status, but the player fixes it by typing a different email.
    const error = mapErrorResponse(409, envelope('email_already_registered'));

    expect(error.recovery).toBe('requires-user-correction');
  });

  it('survives a response that is not the envelope at all', () => {
    // A 502 from a load balancer is HTML. It must still arrive as a server error the
    // retry policy can act on, not as a decode failure.
    const error = mapErrorResponse(502, '<html>Bad Gateway</html>');

    expect(error.kind).toBe('server');
    expect(error.recovery).toBe('retryable-automatically');
    expect(error.message).toContain('502');
  });

  it('survives an absent body', () => {
    expect(mapErrorResponse(500, undefined).kind).toBe('server');
  });
});

describe('transport and decode failures', () => {
  it('classifies an unreachable server as automatically retryable', () => {
    const error = mapTransportFailure(new TypeError('Network request failed'));

    // Nothing reached the server, so this says nothing about the session's validity.
    // Destroying a valid session because a request failed is the worst outcome here.
    expect(error.kind).toBe('network-unavailable');
    expect(error.recovery).toBe('retryable-automatically');
    expect(error.invalidatesSession).toBe(false);
  });

  it('classifies an unreadable response as terminal', () => {
    expect(mapDecodeFailure(new SyntaxError('Unexpected token')).kind).toBe('unknown');
  });
});
