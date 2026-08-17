import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EnvironmentBadge } from "./EnvironmentBadge";
import { ENVIRONMENT_BADGE, ENVIRONMENTS } from "./environment";

/**
 * Every case passes the environment explicitly. The component's default reads the
 * server-only configuration, and a test that let it do so would be testing the process
 * environment rather than the component — which is the reason the override exists.
 */
describe("EnvironmentBadge", () => {
  it.each(["local", "development", "staging"] as const)("renders the %s badge", (environment) => {
    render(<EnvironmentBadge environment={environment} />);

    expect(screen.getByText(ENVIRONMENT_BADGE[environment] as string)).toBeInTheDocument();
  });

  it("renders nothing at all in production", () => {
    const { container } = render(<EnvironmentBadge environment="production" />);

    expect(container).toBeEmptyDOMElement();
  });

  /**
   * Not an empty overlay — a fixed-position element with nothing in it still sits on top
   * of every page in the app.
   */
  it("renders no element in production, not an empty one", () => {
    const { container } = render(<EnvironmentBadge environment="production" />);

    expect(container.querySelector("div")).toBeNull();
  });

  it("badges every environment the table badges, and only those", () => {
    for (const environment of ENVIRONMENTS) {
      const { container, unmount } = render(<EnvironmentBadge environment={environment} />);
      const badged = !(container.childElementCount === 0);

      expect(badged).toBe(ENVIRONMENT_BADGE[environment] !== null);
      unmount();
    }
  });

  /**
   * The word is the accessible name: a screen reader reads the badge because it is text,
   * not because of an ARIA attribute. Deliberately not hidden — this never reaches a club,
   * and a developer using a screen reader needs the fact a sighted one gets.
   */
  it("exposes the badge as readable text rather than as decoration", () => {
    render(<EnvironmentBadge environment="local" />);

    const badge = screen.getByText("LOCAL");

    expect(badge).toBeVisible();
    expect(badge).not.toHaveAttribute("aria-hidden");
  });

  /**
   * The badge is a Server Component. If a `"use client"` directive ever appears in this
   * module the environment would have to reach the browser to render it, which is the one
   * thing the whole design refuses. React marks client modules with `$$typeof`
   * client-reference; a plain function is what a Server Component compiles to.
   */
  it("is a plain component, not a client reference", () => {
    expect(typeof EnvironmentBadge).toBe("function");
    expect(EnvironmentBadge).not.toHaveProperty("$$typeof");
  });
});
