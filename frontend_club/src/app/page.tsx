import { redirect } from 'next/navigation';

import { hasSession } from '@/features/sign-in/queries';

export default async function Home() {
  redirect((await hasSession()) ? '/overview' : '/sign-in');
}
