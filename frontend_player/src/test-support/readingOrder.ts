/**
 * **What a screen reader meets, in order** — a rendered tree walked depth first.
 *
 * **In `test-support/` because two suites ask the same question** (#784): where a field's refusal
 * sits — on the label's row or under the box — and the order the sign-in stage's form reads in.
 * Where a thing sits on the screen is not something a query can see; the order a listener meets it
 * in is, and for a column it is the same fact.
 *
 * Each box is `box:<name>`; each button, link or tick box is `<role>:<name>`, never its insides; a header or
 * an alert is `<role>:<its words>`; every other word is itself. Hidden elements are walked too —
 * a suite that cares picks the items it wants with `inOrder`.
 *
 * **An image is `image:<name>`, never its insides** (#836): a picture spoken whole — the game
 * details' overlap grid — is one element to a listener, its letters and grade the drawing's.
 */

/** A host element as `screen.toJSON()` hands it over — only what the walk reads. */
interface Node {
  readonly type: string;
  readonly props: Readonly<Record<string, unknown>>;
  readonly children: readonly (Node | string)[] | null;
}

type Rendered = Node | readonly Node[] | string | null;

/** `Array.isArray` does not narrow a readonly array; this does. */
const isList = (node: Rendered): node is readonly Node[] => Array.isArray(node);

export function readingOrder(tree: Rendered): string[] {
  const order: string[] = [];
  const walk = (node: Rendered | undefined): void => {
    if (node === null || node === undefined) return;
    if (typeof node === 'string') {
      order.push(node);
      return;
    }
    if (isList(node)) {
      node.forEach(walk);
      return;
    }
    const role = node.props.accessibilityRole;
    const name = node.props.accessibilityLabel;
    if (node.type === 'TextInput') {
      order.push(`box:${String(name)}`);
      return;
    }
    if (
      (role === 'button' || role === 'link' || role === 'checkbox' || role === 'image') &&
      typeof name === 'string'
    ) {
      order.push(`${role}:${name}`);
      return;
    }
    if (role === 'header' || role === 'alert') {
      order.push(`${role}:${wordsOf(node.children)}`);
      return;
    }
    node.children?.forEach(walk);
  };
  walk(tree);
  return order;
}

/**
 * **The part of the tree under the host element with this `testID`** — one screen of a stack, whose
 * screens behind stay rendered with answers of their own (#836). Nothing when there is none.
 */
export function partOf(tree: Rendered, testID: string): Node | null {
  if (tree === null || typeof tree === 'string') return null;
  if (isList(tree)) {
    for (const node of tree) {
      const found = partOf(node, testID);
      if (found !== null) return found;
    }
    return null;
  }
  if (tree.props.testID === testID) return tree;
  for (const child of tree.children ?? []) {
    const found = partOf(child, testID);
    if (found !== null) return found;
  }
  return null;
}

/** `wanted`, in the order the tree meets them — everything else on the screen dropped. */
export function inOrder(tree: Rendered, wanted: readonly string[]): string[] {
  return readingOrder(tree).filter((item) => wanted.includes(item));
}

function wordsOf(children: Node['children']): string {
  return (children ?? [])
    .map((child) => (typeof child === 'string' ? child : wordsOf(child.children)))
    .join('');
}
