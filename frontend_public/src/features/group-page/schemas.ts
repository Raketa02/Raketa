/**
 * **What a code could be**: letters and digits, a group link's and a friend link's alike (the
 * friends mechanics §4.1). The code arrives in the address, so it is untrusted route input
 * (ADR-0187 §7); anything else leads nowhere without asking the backend, and nothing but letters
 * and digits is ever put into a link this site draws.
 */
const A_CODE = /^[a-z0-9]{1,64}$/i;

export function isACode(value: string): boolean {
  return A_CODE.test(value);
}
