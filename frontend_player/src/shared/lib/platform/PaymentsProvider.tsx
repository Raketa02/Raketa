/**
 * How a screen reaches the payment provider's phone half without knowing which one it is —
 * `ShareProvider`'s shape, for its reasons: the default is the real device, so nothing in the app
 * wires this up, and what the provider is for is a test wrapping the tree in a provider that behaves
 * as Stripe's test cards do.
 */

import { createContext, useContext, type ReactNode } from 'react';

import { devicePayments, type PaymentsPort } from './payments';

const PaymentsContext = createContext<PaymentsPort>(devicePayments);

export interface PaymentsProviderProps {
  readonly port: PaymentsPort;
  readonly children: ReactNode;
}

export function PaymentsProvider({ port, children }: PaymentsProviderProps) {
  return <PaymentsContext.Provider value={port}>{children}</PaymentsContext.Provider>;
}

/** The payment provider this tree is running against. The device's, unless a test said otherwise. */
export function usePayments(): PaymentsPort {
  return useContext(PaymentsContext);
}
