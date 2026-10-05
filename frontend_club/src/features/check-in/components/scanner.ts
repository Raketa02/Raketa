import jsQR from 'jsqr';

/**
 * **The camera, and the codes it sees** (the screens B6): the device's back camera, and every QR
 * code in its frames read by jsQR, a decoder in plain JavaScript. Every browser runs it, which a
 * desk's tablet needs: Safari has no `BarcodeDetector`, and the camera opens only on a secure
 * page (`https://`, or this computer).
 */

/** Why the camera is not showing anything: the page says so, and the box still takes a code. */
export type CameraTrouble = 'unsupported' | 'blocked' | 'missing' | 'failed';

/** How long between two frames read: at once to the desk, and easy on a phone. */
const EVERY_MS = 200;

/** A frame is read no wider or taller than this: a QR code held up still has pixels to spare. */
const LONGEST_SIDE = 640;

/**
 * Frames read in a row without a code before it counts as taken away: a second. A frame blurred
 * while the phone is held up misses it too, so one miss is not enough.
 */
const GONE_AFTER = 5;

function troubleOf(error: unknown): CameraTrouble {
  const name = error instanceof DOMException ? error.name : '';
  if (name === 'NotAllowedError' || name === 'SecurityError') return 'blocked';
  if (name === 'NotFoundError' || name === 'OverconstrainedError') return 'missing';
  return 'failed';
}

/** **Open the back camera**, or say why it would not open. */
export async function openCamera(): Promise<MediaStream | CameraTrouble> {
  // Undefined on a page that is not secure, and in a browser with no camera API at all.
  const devices = navigator.mediaDevices as MediaDevices | undefined;
  if (devices === undefined || typeof devices.getUserMedia !== 'function') return 'unsupported';
  try {
    return await devices.getUserMedia({
      audio: false,
      video: { facingMode: { ideal: 'environment' } },
    });
  } catch (error) {
    return troubleOf(error);
  }
}

/**
 * **Read the QR codes the video shows**, until the function it returns is called, handing each
 * one's text to `onHeldUp` **once each time it is held up**: read on every frame while it stays
 * in view, a code is new again only after it has been taken away, or another has been read.
 */
export function readCodes(video: HTMLVideoElement, onHeldUp: (text: string) => void): () => void {
  const canvas = document.createElement('canvas');
  const context = canvas.getContext('2d', { willReadFrequently: true });
  let timer: number | undefined;
  let held: string | null = null;
  let unseen = 0;

  const saw = (text: string | null) => {
    if (text === null) {
      unseen += 1;
      if (unseen >= GONE_AFTER) held = null;
      return;
    }
    unseen = 0;
    if (text === held) return;
    held = text;
    onHeldUp(text);
  };

  const look = () => {
    if (context !== null && video.readyState >= video.HAVE_CURRENT_DATA && video.videoWidth > 0) {
      const scale = Math.min(1, LONGEST_SIDE / Math.max(video.videoWidth, video.videoHeight));
      const width = Math.round(video.videoWidth * scale);
      const height = Math.round(video.videoHeight * scale);
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width;
        canvas.height = height;
      }
      context.drawImage(video, 0, 0, width, height);
      const { data } = context.getImageData(0, 0, width, height);
      // A phone shows dark modules on white, so the inverted image is never tried.
      const found = jsQR(data, width, height, { inversionAttempts: 'dontInvert' });
      saw(found === null || found.data === '' ? null : found.data);
    }
    timer = window.setTimeout(look, EVERY_MS);
  };
  look();
  return () => window.clearTimeout(timer);
}
