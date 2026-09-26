import { androidAssetLinks } from '@/features/app-link-files/queries';

/**
 * **Android's asset links**, at the path Android asks for, with no redirect, as JSON. Made per
 * request from the running server's settings, never the build's (e2e/config.spec.ts).
 */
export function GET() {
  return Response.json(androidAssetLinks());
}
