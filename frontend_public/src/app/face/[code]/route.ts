import { faceImage } from '@/features/friend-link/preview';
import { readFaceByLink } from '@/features/friend-link/queries';

/**
 * **A friend link's face**, `/face/<code>`: the owner's photograph, square, which the page draws
 * and its preview tags name. Outside `/f/`, which the app claims on a phone with Rakieta installed.
 * A link that leads nowhere, and somebody with no photograph, have no picture.
 */
export async function GET(_request: Request, { params }: { params: Promise<{ code: string }> }) {
  const { code } = await params;
  const face = await readFaceByLink(code);
  if (face === null) return new Response(null, { status: 404 });
  return faceImage(face);
}
