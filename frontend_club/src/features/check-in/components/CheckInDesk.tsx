'use client';

import { startTransition, useActionState, useRef } from 'react';

import { checkIn, type CheckInState } from '../actions';
import type { Via } from '../schemas';

import { Camera } from './Camera';
import { CheckInAnswer } from './CheckInAnswer';
import styles from './CheckIn.module.css';
import { CodeForm } from './CodeForm';

const NOTHING_YET: CheckInState = {
  via: null,
  checkedIn: null,
  refusal: null,
  refusals: {},
  formRefusal: null,
};

/**
 * **The desk** (the screens B6): the camera, the last code's answer under it, and the box for a
 * short code under that. Both ways in go through the one action, so the answer is always about
 * the last code, however it came.
 */
export function CheckInDesk() {
  const [state, dispatch, checking] = useActionState(checkIn, NOTHING_YET);
  // The code the camera last read, for *Try again* when the server could not be asked about it.
  const lastScan = useRef<string | null>(null);

  const send = (via: Via, code: string) => {
    const form = new FormData();
    form.set('via', via);
    form.set('code', code);
    startTransition(() => dispatch(form));
  };

  return (
    <div className={styles.desk}>
      <Camera
        onHeldUp={(text) => {
          lastScan.current = text;
          send('camera', text);
        }}
      />
      <CheckInAnswer
        state={state}
        checking={checking}
        onTryAgain={() => {
          if (lastScan.current !== null) send('camera', lastScan.current);
        }}
      />
      <CodeForm state={state} action={dispatch} checking={checking} />
    </div>
  );
}
