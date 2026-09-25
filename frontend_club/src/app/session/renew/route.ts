import { redirect } from 'next/navigation';
import type { NextRequest } from 'next/server';

import { renewSession } from '@/server/club';

/**
 * **Where a render hands a refused pair** (`src/server/club.ts`): a route handler can set the
 * cookie a render cannot. It renews through the single flight and sends the browser back, or on
 * to sign-in.
 */
export async function GET(request: NextRequest) {
  redirect(await renewSession(request.nextUrl.searchParams.get('to') ?? ''));
}
