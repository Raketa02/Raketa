'use client';

import { startTransition, type ReactNode } from 'react';

/**
 * **A form that keeps what was typed.** React resets a form after every `action` submission
 * with the native `form.reset()`, which puts a controlled checkbox back to unticked though its
 * state still says ticked: a refused sign-up lost its sports. So a submission goes through
 * `onSubmit`, inside a transition (which is what keeps `useActionState`'s pending flag), and
 * nothing is reset. The `action` stays on the element for a browser without JavaScript.
 *
 * `noValidate`: every refusal is this site's own sentence under its field, never a browser
 * bubble.
 */
export function Form({
  action,
  className,
  onSent,
  children,
}: {
  action: (form: FormData) => void;
  className?: string;
  /** Called once a submission is on its way: a question in a dialog closes. */
  onSent?: () => void;
  children: ReactNode;
}) {
  return (
    <form
      action={action}
      noValidate
      className={className}
      onSubmit={(event) => {
        event.preventDefault();
        const submitter = (event.nativeEvent as SubmitEvent).submitter;
        const form = new FormData(event.currentTarget, submitter);
        startTransition(() => action(form));
        onSent?.();
      }}
    >
      {children}
    </form>
  );
}
