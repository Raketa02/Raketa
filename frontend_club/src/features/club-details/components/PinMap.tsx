'use client';

import 'leaflet/dist/leaflet.css';

import L from 'leaflet';
import { useEffect, useEffectEvent, useRef } from 'react';

import type { MapPoint } from '../mappers';

import styles from './PinMap.module.css';

/**
 * **The map the desk drops the club's pin on**: OpenStreetMap tiles, with their attribution,
 * from the tile URL the server is configured with (ADR-0187 §3 and §7).
 *
 * A click or a tap drops the pin, and dragging it moves it. The map is focusable and pans with
 * the arrow keys, and the handle's `centre` puts the pin in the middle, so a keyboard can place
 * it too. The handle's `show` takes the map to a point at the pin's own zoom: the address search
 * moves the view there and the owner moves the pin.
 *
 * Loaded in the browser only (`ssr: false`): Leaflet reads `window` when it is imported. The
 * container says `data-ready="true"` once the map is drawn, for anything that waits on it.
 */

const ATTRIBUTION =
  '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors';

/** Close enough to see the street; the pin's own view. */
const PINNED_ZOOM = 16;
/** The city, before there is a pin. */
const START_ZOOM = 13;
const MAX_ZOOM = 19;

function toLatLng(point: MapPoint): L.LatLngTuple {
  return [point.latitude, point.longitude];
}

function fromLatLng(latlng: L.LatLng): MapPoint {
  return { latitude: latlng.lat, longitude: latlng.lng };
}

export interface PinMapHandle {
  centre(): void;
  /** Take the view to `point`, close enough to see the street. The pin is the owner's to move. */
  show(point: MapPoint): void;
}

export function PinMap({
  tileUrl,
  start,
  value,
  onChange,
  label,
  describedBy,
  onReady,
}: {
  tileUrl: string;
  start: MapPoint;
  value: MapPoint | null;
  onChange: (point: MapPoint) => void;
  label: string;
  describedBy?: string;
  onReady?: (handle: PinMapHandle) => void;
}) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<L.Map | null>(null);
  const marker = useRef<L.Marker | null>(null);

  const place = useEffectEvent((point: MapPoint) => onChange(point));
  const firstView = useEffectEvent(() => ({ pinned: value, start }));
  const announce = useEffectEvent((handle: PinMapHandle) => onReady?.(handle));

  /** Put the marker where `point` says, making it on the first pin and taking it away on none. */
  const pinTo = useEffectEvent((point: MapPoint | null) => {
    const current = map.current;
    if (current === null) return;
    if (point === null) {
      marker.current?.remove();
      marker.current = null;
    } else if (marker.current === null) {
      const created = L.marker(toLatLng(point), {
        draggable: true,
        keyboard: false,
        // An explicit `undefined` overrides the div icon's 12 × 12 default, so Leaflet writes no
        // size or margin inline and the pin's own class sizes and anchors it from the tokens.
        icon: L.divIcon({ className: styles.pin, iconSize: undefined }),
      });
      created.on('dragend', () => place(fromLatLng(created.getLatLng())));
      created.addTo(current);
      marker.current = created;
    } else {
      marker.current.setLatLng(toLatLng(point));
    }
  });

  useEffect(() => {
    const element = container.current;
    if (element === null) return;
    const { pinned, start: opening } = firstView();
    const created = L.map(element, {
      center: toLatLng(pinned ?? opening),
      zoom: pinned === null ? START_ZOOM : PINNED_ZOOM,
      scrollWheelZoom: false,
    });
    L.tileLayer(tileUrl, { attribution: ATTRIBUTION, maxZoom: MAX_ZOOM }).addTo(created);
    created.attributionControl.setPrefix(false);
    created.on('click', (event: L.LeafletMouseEvent) => place(fromLatLng(event.latlng)));
    map.current = created;
    pinTo(pinned);
    announce({
      centre: () => place(fromLatLng(created.getCenter())),
      show: (point) => created.setView(toLatLng(point), PINNED_ZOOM),
    });
    element.dataset.ready = 'true';
    return () => {
      delete element.dataset.ready;
      created.remove();
      map.current = null;
      marker.current = null;
    };
  }, [tileUrl]);

  useEffect(() => {
    pinTo(value);
  }, [value]);

  return (
    <div
      ref={container}
      className={styles.map}
      role="region"
      aria-label={label}
      aria-describedby={describedBy}
    />
  );
}
