import { ratingPosition, toggleSport } from "./sportQueue";

describe("choosing sports", () => {
  it("keeps the order they were chosen in", () => {
    let queue = toggleSport([], "tennis");
    queue = toggleSport(queue, "padel");

    // Not registry order: the first sport tapped is the first assessment, and that is the
    // only thing the order means.
    expect(queue).toEqual(["tennis", "padel"]);
  });

  it("removes a sport that was already chosen", () => {
    expect(toggleSport(["tennis", "padel", "squash"], "padel")).toEqual([
      "tennis",
      "squash",
    ]);
  });

  it("does not mutate the queue it was given", () => {
    const queue = ["tennis"] as const;
    toggleSport(queue, "padel");
    expect(queue).toEqual(["tennis"]);
  });
});

describe("position across sports", () => {
  it("counts the sport's place in the queue", () => {
    expect(ratingPosition(["tennis", "padel"], "padel")).toEqual({ index: 2, total: 2 });
  });

  it("treats a sport outside the queue as a run of one", () => {
    // The resumed case. The queue was never persisted, so a player returning to an
    // unfinished padel assessment is rating exactly one sport as far as anyone can know.
    expect(ratingPosition([], "padel")).toEqual({ index: 1, total: 1 });
  });
});
