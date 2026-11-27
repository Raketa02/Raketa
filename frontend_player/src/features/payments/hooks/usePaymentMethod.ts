/**
 * **The saved method, and the two things done to it in place** — removing it, and accepting the
 * terms again after the bank moved it to another brand (#552; the mechanics §12.5).
 *
 * One read, `GET …/current`, behind the You tab's row and the Payments screen alike. A removal
 * writes *nothing saved* into it at once — the screen is state A the moment the server agrees —
 * and a re-accepted term re-reads it, because what the terms answered is not the method.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import type { AppError } from '@/shared/errors';

import type { PaymentMethodStanding } from '../domain/vocabulary';
import {
  acceptTerms,
  readPaymentMethod,
  removalRefusal,
  removePaymentMethod,
} from '../use-cases/paymentMethod';

import { paymentKeys } from './paymentKeys';

/** The reader's saved method — the read, as its observers ask it and a screen reads it ahead. */
export function paymentMethodQuery() {
  return {
    queryKey: paymentKeys.current(),
    queryFn: ({ signal }: { signal: AbortSignal }) => readPaymentMethod({ signal }),
  };
}

export function usePaymentMethod() {
  return useQuery<PaymentMethodStanding, AppError>(paymentMethodQuery());
}

/**
 * **Whether a yes must wait for a saved method** — *before your first yes, the app asks you once*
 * (the mechanics §6.1, §12.5; the screens A2.4). `true` with nothing saved; `false` with a method;
 * `undefined` while the read has not answered, when the yes is sent and the server decides
 * (`payment_method_required`).
 */
export function usePaymentSetupNeeded(): boolean | undefined {
  const standing = usePaymentMethod().data;
  return standing === undefined ? undefined : standing.method === null;
}

/** *Remove this method* — refused with its reason while anything live needs it (Q83). */
export function useRemovePaymentMethod() {
  const client = useQueryClient();

  const removal = useMutation<void, AppError, void>({
    mutationFn: () => removePaymentMethod(),
    onSuccess: () => {
      client.setQueryData<PaymentMethodStanding>(paymentKeys.current(), {
        method: null,
        termsNeeded: false,
      });
    },
    onError: (error) => {
      // Removed elsewhere: the read is what is wrong, and re-reading it is the whole answer.
      if (removalRefusal(error).kind === 'GONE') {
        void client.invalidateQueries({ queryKey: paymentKeys.current() });
      }
    },
  });

  return {
    remove: () => removal.mutate(),
    isPending: removal.isPending,
    refusal: removal.error === null ? null : removalRefusal(removal.error),
  };
}

/**
 * *Accept the terms* again, for the card already saved — no setup, nothing to confirm. Made online
 * or not at all, as the setup's own acceptance is (`usePaymentSetup`): one press the player waits
 * on, which should say *couldn't reach Raketa* now rather than land minutes later.
 */
export function useAcceptTermsAgain() {
  const client = useQueryClient();

  return useMutation<string | null, AppError, string>({
    networkMode: 'always',
    mutationFn: (termsVersion) => acceptTerms(termsVersion),
    onSuccess: () => client.invalidateQueries({ queryKey: paymentKeys.current() }),
  });
}
