/**
 * A rendered node printed as the element it is — for the test process only
 * ([#493](https://github.com/Raketa02/Raketa/issues/493)).
 *
 * ## What this fixes
 *
 * A failing matcher prints what it received, and a query hands back a `ReactTestInstance`, whose
 * one own property is its fiber — the whole tree, every way, through `return`, `child`, `sibling`
 * and `alternate`. `pretty-format` walks it ten levels deep, and again shallower and narrower
 * each time the result is too long to show: a third of a second on this app's route tree, for a
 * message nobody could read.
 *
 * Inside a `waitFor` that is paid on every poll that has not passed yet. A test that waits out a
 * row with `waitFor(() => expect(queryBy…(…)).toBeNull())` spent about a second formatting, and
 * on a starved runner more than five — the whole of a test's budget, with every assertion in it
 * passing. `deck.test.tsx` spends half its time there: 51 s without this, 25 s with it. Its
 * memory is another matter, and not this module's — see `schedulerClock.ts` (#494).
 *
 * ## What a node prints as now
 *
 * Its type and its props, children left out — `<View accessibilityLabel="…" … />`, through
 * `pretty-format`'s own plugin for the renderer's JSON, which a `toJSON` on the node is read
 * through. Nothing compares nodes by it: equality reads own properties, and this is on the
 * prototype.
 *
 * The class is not exported, so it is taken off the root of a throwaway render — which loads the
 * renderer, so this is installed after `schedulerClock.ts` has pointed the renderer's scheduler
 * at its clock. `nodePrinting.test.tsx` pins it.
 *
 * Not app code — nothing under `src/` imports this.
 */

import { createElement, type ReactElement } from 'react';

/** What `pretty-format`'s `ReactTestComponent` plugin prints as `<type prop="…" />`. */
interface PrintedElement {
  readonly $$typeof: symbol;
  readonly type: string;
  readonly props: Readonly<Record<string, unknown>>;
  readonly children: null;
}

/** A node as the renderer hands one out: a host type's name, or the component itself. */
interface RenderedNode {
  readonly type: string | { readonly displayName?: string; readonly name?: string };
  readonly props: Readonly<Record<string, unknown>>;
}

/** The part of the renderer this reaches — the package ships no types. */
interface TestRenderer {
  create: (element: ReactElement) => {
    readonly root: { readonly constructor: { readonly prototype: object } };
    unmount: () => void;
  };
}

function printed(node: RenderedNode): PrintedElement {
  const { children: _children, ...props } = node.props;
  const type =
    typeof node.type === 'string' ? node.type : (node.type.displayName ?? node.type.name ?? '');
  return { $$typeof: Symbol.for('react.test.json'), type, props, children: null };
}

/** Make every rendered node print as its element. Called once, from `jest.setup.js`. */
export function printNodesAsElements(): void {
  const probe = jest
    .requireActual<TestRenderer>('react-test-renderer')
    .create(createElement('probe'));
  const nodes = probe.root.constructor.prototype;
  probe.unmount();

  Object.assign(nodes, {
    toJSON(this: RenderedNode): PrintedElement {
      return printed(this);
    },
  });
}
