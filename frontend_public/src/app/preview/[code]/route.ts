import { previewImage } from '@/features/group-page/preview';
import { readGroupByLink } from '@/features/group-page/queries';

/**
 * **The preview's image**, `/preview/<code>`: the group's tile, which the group page's preview
 * tags name. Outside `/join/`, which the app claims on a phone with Raketa installed. A link that
 * leads nowhere has no picture.
 */
export async function GET(_request: Request, { params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const group = await readGroupByLink(code);
  if (group === null) return new Response(null, { status: 404 });
  return previewImage(group);
}
