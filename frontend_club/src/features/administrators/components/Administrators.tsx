'use client';

import { useActionState, useState } from 'react';

import { Button } from '@/ui/Button';
import { SITE_COPY } from '@/ui/copy';
import { Notice } from '@/ui/Notice';
import { PageHeader } from '@/ui/PageHeader';

import {
  actOnAdministrator,
  inviteAdministrator,
  type ActState,
  type InviteState,
} from '../actions';
import { actRefusal, ADMINISTRATORS_COPY as COPY } from '../copy';
import type { Administrator, Sent } from '../mappers';

import { AdministratorsTable } from './AdministratorsTable';
import { InviteForm } from './InviteForm';
import { RemoveDialog } from './RemoveDialog';
import { SentBanner } from './SentBanner';

const NOTHING_SENT: InviteState = { refusals: {}, formRefusal: null, sent: null };
const NOTHING_DONE: ActState = { sent: null, refusal: null };

/**
 * **Administrators** (#500 stories 96–104): the people who run the club's groups in the app,
 * and the one way to add one. *+ Add administrator* gives way to its form while the form is
 * open; a sent invitation closes the form. The banner and the notice over the table say what the
 * last act came to, until the next one, or until the form opens again.
 */
export function Administrators({ administrators }: { administrators: readonly Administrator[] }) {
  const [inviteState, invite, inviting] = useActionState(inviteAdministrator, NOTHING_SENT);
  const [seenInvite, setSeenInvite] = useState(inviteState);
  const [actState, act, acting] = useActionState(actOnAdministrator, NOTHING_DONE);
  const [seenAct, setSeenAct] = useState(actState);

  const [adding, setAdding] = useState(false);
  // What the open form shows of the backend's answers: none from before it was opened.
  const [formState, setFormState] = useState(NOTHING_SENT);
  const [sent, setSent] = useState<Sent | null>(null);
  const [refused, setRefused] = useState<ActState['refusal']>(null);
  const [removing, setRemoving] = useState<Administrator | null>(null);

  // A new answer: adjust during render, as React recommends over an effect.
  if (seenInvite !== inviteState) {
    setSeenInvite(inviteState);
    if (inviteState.sent === null) setFormState(inviteState);
    else {
      setAdding(false);
      setSent(inviteState.sent);
      setRefused(null);
    }
  }
  if (seenAct !== actState) {
    setSeenAct(actState);
    setSent(actState.sent);
    setRefused(actState.refusal);
  }

  return (
    <>
      <PageHeader
        caption={COPY.caption}
        title={SITE_COPY.frame.pages.administrators}
        aside={
          adding ? undefined : (
            <Button
              type="button"
              onClick={() => {
                setFormState(NOTHING_SENT);
                setSent(null);
                setRefused(null);
                setAdding(true);
              }}
            >
              {COPY.add}
            </Button>
          )
        }
      />
      {adding ? (
        <InviteForm
          state={formState}
          action={invite}
          pending={inviting}
          onCancel={() => setAdding(false)}
        />
      ) : null}
      {sent === null ? null : <SentBanner sent={sent} onDone={() => setSent(null)} />}
      {refused === null ? null : <Notice tone="error">{actRefusal(refused)}</Notice>}
      <AdministratorsTable
        administrators={administrators}
        action={act}
        pending={acting}
        onRemove={setRemoving}
      />
      <RemoveDialog administrator={removing} action={act} onClose={() => setRemoving(null)} />
    </>
  );
}
