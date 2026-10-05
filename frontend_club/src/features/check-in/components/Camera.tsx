'use client';

import { useEffect, useEffectEvent, useRef, useState } from 'react';

import { Button } from '@/ui/Button';
import { Card } from '@/ui/Card';
import { SectionHeader } from '@/ui/SectionHeader';

import { CHECK_IN_COPY } from '../copy';

import styles from './CheckIn.module.css';
import { openCamera, readCodes, type CameraTrouble } from './scanner';

const COPY = CHECK_IN_COPY.camera;

/** What the camera card shows: opening, reading, or why not (it never opened, or it stopped). */
type Seeing = 'opening' | 'reading' | CameraTrouble | 'stopped';

/**
 * **The camera** (the screens B6): it opens with the page and closes with it, and hands each code
 * to `onHeldUp` once each time it is held up. When the browser will not open it, or it stops, the
 * card says why, and the camera can be asked for again; the box below takes the code meanwhile.
 */
export function Camera({ onHeldUp }: { onHeldUp: (text: string) => void }) {
  const video = useRef<HTMLVideoElement>(null);
  const [seeing, setSeeing] = useState<Seeing>('opening');
  const [asked, setAsked] = useState(0);
  const heldUp = useEffectEvent((text: string) => onHeldUp(text));

  useEffect(() => {
    const element = video.current;
    if (element === null) return;
    let closed = false;
    let stream: MediaStream | null = null;
    let stopReading = () => {};
    const close = () => {
      stopReading();
      stream?.getTracks().forEach((track) => track.stop());
      element.srcObject = null;
    };

    const open = async () => {
      const opened = await openCamera();
      if (typeof opened === 'string') {
        if (!closed) setSeeing(opened);
        return;
      }
      stream = opened;
      if (closed) {
        close();
        return;
      }
      element.srcObject = opened;
      // A camera unplugged, or taken by another app, ends its track: the card says so.
      for (const track of opened.getVideoTracks()) {
        track.addEventListener('ended', () => {
          if (closed) return;
          stopReading();
          setSeeing('stopped');
        });
      }
      try {
        await element.play();
      } catch {
        if (!closed) setSeeing('failed');
        return;
      }
      if (closed) return;
      setSeeing('reading');
      stopReading = readCodes(element, (text) => heldUp(text));
    };

    void open();
    return () => {
      closed = true;
      close();
    };
  }, [asked]);

  const trouble = seeing === 'opening' || seeing === 'reading' ? null : seeing;
  return (
    <Card labelledBy="camera-title">
      <SectionHeader id="camera-title" title={COPY.title} />
      <div className={styles.viewfinder} hidden={trouble !== null}>
        <video ref={video} className={styles.video} aria-label={COPY.label} muted playsInline />
      </div>
      {trouble === null ? (
        <p className={styles.line}>{seeing === 'reading' ? COPY.reading : COPY.opening}</p>
      ) : (
        <div className={styles.trouble}>
          <p>{COPY.trouble[trouble]}</p>
          {trouble === 'unsupported' ? null : (
            <Button
              type="button"
              tone="secondary"
              onClick={() => {
                setSeeing('opening');
                setAsked((times) => times + 1);
              }}
            >
              {COPY.retry}
            </Button>
          )}
        </div>
      )}
    </Card>
  );
}
