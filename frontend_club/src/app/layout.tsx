/**
 * The root layout — the App Router's single composition point, and today the whole of it.
 *
 * It exists for one reason #99 asked for: `<EnvironmentBadge />` had been built by #96 and
 * **mounted nowhere**, because there was no layout to mount it in. A badge that is not
 * rendered is not a badge; the guarantee it exists to give — *you can never believe you are
 * testing one environment while acting in another* — is only true once it is on the page.
 *
 * It is deliberately the minimum that discharges that, and not the §47 scaffolding pass:
 * no providers, no Query client, no session boundary, no route groups. Those arrive with
 * the features that need them, each with its own reason. What is here is what the design
 * system's contract requires of the *first* layout, and nothing beyond it.
 *
 * **No `"use client"`, here or in anything this renders.** The badge reads the server-only
 * environment; a client boundary at the root would make that impossible and would opt the
 * entire tree out of Server Components (§3.5).
 */

import type { Metadata } from "next";
import { Archivo, IBM_Plex_Mono } from "next/font/google";

import { EnvironmentBadge } from "@/platform/config/EnvironmentBadge";

import "@/shared/ui/tokens.css";

/**
 * The two families the locked design system names, bound to the variables `tokens.css`
 * reads (`--font-sans`, `--font-mono`). `next/font` self-hosts them and emits the
 * `font-display: swap` and size-adjust metrics that stop a late font reflowing every number
 * on screen — which is why they are loaded here rather than with an `@import` in the
 * stylesheet.
 */
const archivo = Archivo({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
  variable: "--font-sans",
  display: "swap",
});

const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  weight: ["400", "500", "600"],
  variable: "--font-mono",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Raketa Club",
  description: "Manage your courts, availability, pricing and bookings.",
};

export default function RootLayout({ children }: { readonly children: React.ReactNode }) {
  return (
    <html lang="en" className={`${archivo.variable} ${plexMono.variable}`}>
      <body>
        {children}
        {/*
         * Last in the body, so the fixed overlay sits above the page without needing a
         * z-index argument with anything. It renders `null` in production, which is why
         * mounting it unconditionally is correct — the environment decides, not the caller.
         */}
        <EnvironmentBadge />
      </body>
    </html>
  );
}
