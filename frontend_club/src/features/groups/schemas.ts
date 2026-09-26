/** **A handover as its form posts it**: which group, to whom, and the name the desk chose. */

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
