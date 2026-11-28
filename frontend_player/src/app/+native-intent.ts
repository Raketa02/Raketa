/**
 * **Every address the operating system opens the app with, read before anything is routed**
 * ([#520](https://github.com/Rakieta02/Rakieta/issues/520)).
 *
 * expo-router calls `redirectSystemPath` with the launch address and with every one opened while the
 * app runs — `rakieta://…` always, the web domain's `https://…` once one is set — and routes to what
 * it answers. The answer is the links feature's: one of the three links — or the app's bare address,
 * the club's email to an existing account — is held and answered where it can be, and **anything
 * else is ignored**, so no address from outside reaches a route by its path
 * (docs/architecture.md Part 2, *Deep links are untrusted input*).
 */

export { redirectSystemPath } from '@/features/links/types';
