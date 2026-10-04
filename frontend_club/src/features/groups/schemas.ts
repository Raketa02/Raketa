/**
 * **What the group page's forms post**: a handover (which group, to whom, and the name the desk
 * chose), and an answer to somebody asking to join.
 */

import { formId, formText } from '@/ui/forms';

export interface HandOverDraft {
  /** `null` when what was posted is no id at all. */
  readonly groupId: string | null;
  readonly administratorId: string | null;
  /** Whom the desk chose, as the page named them: a refusal is said about them. */
  readonly name: string;
}

export function readHandOver(form: FormData): HandOverDraft {
  return {
    groupId: formId(form, 'group'),
    administratorId: formId(form, 'administrator'),
    name: formText(form, 'name'),
  };
}

/** The two answers to somebody asking to join. */
export const ANSWERS = ['approve', 'decline'] as const;
export type Answer = (typeof ANSWERS)[number];

function isAnswer(value: string): value is Answer {
  return (ANSWERS as readonly string[]).includes(value);
}

export interface AnswerDraft {
  /** `null` when what was posted is no id at all. */
  readonly groupId: string | null;
  readonly playerId: string | null;
  /** `null` when what was posted is neither answer. */
  readonly answer: Answer | null;
  /** Whom it answers, as the page named them: a refusal is said about them. */
  readonly name: string;
}

export function readAnswer(form: FormData): AnswerDraft {
  const answer = formText(form, 'answer');
  return {
    groupId: formId(form, 'group'),
    playerId: formId(form, 'player'),
    answer: isAnswer(answer) ? answer : null,
    name: formText(form, 'name'),
  };
}
