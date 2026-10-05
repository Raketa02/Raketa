/**
 * **A camera the suite holds codes up to** (#564): what the Check in page opens instead of the
 * device's own. `getUserMedia` answers with a canvas's stream, and the canvas shows whatever the
 * test holds up: a real QR code, drawn as the player app draws one (error correction M), which
 * the page decodes as it would a phone's screen. Nothing in the site knows; the page asks the
 * browser for a camera and reads the frames it gets.
 *
 * The camera also counts the frames the page has looked at, so a test can say "it kept reading
 * that code and still asked once" without waiting on a clock.
 */

import type { Page } from '@playwright/test';
import { toDataURL } from 'qrcode';

/** Why the browser would not open the camera, as `DOMException`'s name says it. */
export type CameraRefusal = 'NotAllowedError' | 'NotFoundError';

/** What the init script leaves on `window` for the test to reach. */
interface InPage {
  show(source: string | null): Promise<void>;
  /** End every track handed out, as a camera unplugged or taken by another app ends its own. */
  unplug(): void;
  refusal: CameraRefusal | null;
  looks: number;
}

type Suite = { suiteCamera: InPage };

export interface FakeCamera {
  /** Hold up a QR code of `text`, as a player's phone shows it at the desk. */
  show(text: string): Promise<void>;
  /** Take it away: the camera sees an empty desk. */
  clear(): Promise<void>;
  /** The camera stops while the page is reading it. */
  unplug(): Promise<void>;
  /** Let the browser open the camera from now on: the desk allowed it. */
  allow(): Promise<void>;
  /** Wait until the page has looked at `frames` more frames than it had when this was called. */
  lookedAtMore(frames: number): Promise<void>;
}

/**
 * **Give the page a fake camera**, before it loads: one that works, or one the browser refuses
 * with `refusal`, as a blocked or a missing camera is refused.
 */
export async function fakeCamera(
  page: Page,
  { refusal = null }: { refusal?: CameraRefusal | null } = {},
): Promise<FakeCamera> {
  await page.addInitScript((refused) => {
    const canvas = document.createElement('canvas');
    canvas.width = 640;
    canvas.height = 480;
    const context = canvas.getContext('2d');
    let shown: HTMLImageElement | null = null;
    const streams: MediaStream[] = [];
    const camera: InPage = {
      refusal: refused,
      looks: 0,
      unplug: () => {
        for (const stream of streams) {
          for (const track of stream.getVideoTracks()) track.dispatchEvent(new Event('ended'));
        }
      },
      show: (source) =>
        new Promise<void>((resolve) => {
          if (source === null) {
            shown = null;
            resolve();
            return;
          }
          const image = new Image();
          image.onload = () => {
            shown = image;
            resolve();
          };
          image.src = source;
        }),
    };
    (window as unknown as Suite).suiteCamera = camera;

    // A stream only carries a frame when its canvas is drawn on, so it is drawn on all the time.
    const paint = () => {
      if (context === null) return;
      context.fillStyle = '#ffffff';
      context.fillRect(0, 0, canvas.width, canvas.height);
      if (shown !== null) context.drawImage(shown, 170, 90, 300, 300);
    };
    paint();
    setInterval(paint, 40);

    // The page reads a frame by drawing the video onto a canvas of its own: that is a look.
    const draw = CanvasRenderingContext2D.prototype.drawImage;
    CanvasRenderingContext2D.prototype.drawImage = function (
      this: CanvasRenderingContext2D,
      ...args: unknown[]
    ) {
      if (args[0] instanceof HTMLVideoElement) camera.looks += 1;
      return (draw as (...each: unknown[]) => void).apply(this, args);
    };

    navigator.mediaDevices.getUserMedia = () => {
      if (camera.refusal !== null) {
        return Promise.reject(new DOMException('The suite refused the camera.', camera.refusal));
      }
      const stream = canvas.captureStream(25);
      streams.push(stream);
      return Promise.resolve(stream);
    };
  }, refusal);

  return {
    async show(text) {
      const source = await toDataURL(text, { errorCorrectionLevel: 'M', margin: 4, width: 300 });
      await page.evaluate((image) => (window as unknown as Suite).suiteCamera.show(image), source);
    },
    async clear() {
      await page.evaluate(() => (window as unknown as Suite).suiteCamera.show(null));
    },
    async unplug() {
      await page.evaluate(() => (window as unknown as Suite).suiteCamera.unplug());
    },
    async allow() {
      await page.evaluate(() => {
        (window as unknown as Suite).suiteCamera.refusal = null;
      });
    },
    async lookedAtMore(frames) {
      const now = await page.evaluate(() => (window as unknown as Suite).suiteCamera.looks);
      await page.waitForFunction(
        (until) => (window as unknown as Suite).suiteCamera.looks >= until,
        now + frames,
      );
    },
  };
}
