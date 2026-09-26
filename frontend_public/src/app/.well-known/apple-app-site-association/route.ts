import { appleAssociation } from '@/features/app-link-files/queries';

/**
 * **Apple's association file**, at the path iOS asks for, with no extension and no redirect, as
 * JSON. Made per request from the running server's settings, never the build's
 * (e2e/config.spec.ts).
 */
export function GET() {
  return Response.json(appleAssociation());
}
