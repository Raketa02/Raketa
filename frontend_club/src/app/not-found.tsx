import { AuthCard } from '@/ui/AuthCard';
import { SITE_COPY } from '@/ui/copy';
import { TextLink } from '@/ui/TextLink';

export default function NotFound() {
  return (
    <AuthCard title={SITE_COPY.notFound.title} lead={SITE_COPY.notFound.lead}>
      <TextLink href="/">{SITE_COPY.notFound.home}</TextLink>
    </AuthCard>
  );
}
