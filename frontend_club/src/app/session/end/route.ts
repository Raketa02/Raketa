import { redirect } from 'next/navigation';

import { endRefusedSession } from '@/server/club';

/** **Where a pair refused as soon as it was issued ends**: the cookie goes, and sign-in says so. */
export async function GET() {
  redirect(await endRefusedSession());
}
