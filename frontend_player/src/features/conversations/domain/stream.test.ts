/**
 * The one rule the optimistic send has: **a message replaces itself, never joins itself.**
 */

import type { Entry } from './entry';
import { newClientMessageId, streamOf, type SendingMessage } from './stream';

const ME = 'me';

function landed(seq: number, clientMessageId: string): Entry {
  return {
    kind: 'message',
    seq,
    authorId: ME,
    sentAt: '2026-09-12T08:00:00Z',
    text: 'landed',
    clientMessageId,
  };
}

function line(seq: number): Entry {
  return {
    kind: 'system-line',
    seq,
    code: 'SEAT_ACCEPTED',
    occurredAt: '2026-09-12T07:00:00Z',
    values: {},
  };
}

function sending(clientMessageId: string): SendingMessage {
  return { kind: 'sending', clientMessageId, authorId: ME, text: 'going out' };
}

it('draws what is going out after what has landed', () => {
  expect(streamOf([line(1)], [sending('c-1')])).toEqual([line(1), sending('c-1')]);
});

/** A resumed send answers with the message it already made. Two bubbles would be the defect. */
it('drops a send whose message is already in the backlog', () => {
  expect(streamOf([landed(2, 'c-1')], [sending('c-1')])).toEqual([landed(2, 'c-1')]);
});

it('keeps a send whose message is not there yet, beside one whose is', () => {
  expect(streamOf([landed(2, 'c-1')], [sending('c-1'), sending('c-2')])).toEqual([
    landed(2, 'c-1'),
    sending('c-2'),
  ]);
});

/** A system line has no `clientMessageId` and must never be read as one. */
it('never matches a send against a system line', () => {
  expect(streamOf([line(1)], [sending('c-1')])).toHaveLength(2);
});

describe('a fresh client message id', () => {
  it('is a version-4 UUID, which is what the field is on the wire', () => {
    for (let made = 0; made < 50; made += 1) {
      expect(newClientMessageId()).toMatch(
        /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/,
      );
    }
  });

  it('is a different one every time', () => {
    const made = Array.from({ length: 200 }, newClientMessageId);
    expect(new Set(made).size).toBe(made.length);
  });
});
