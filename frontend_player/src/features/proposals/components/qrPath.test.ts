import { qrDrawing, darkRunsPath } from './qrPath';

describe('darkRunsPath — the dark modules as one path, a run at a time', () => {
  it('draws each run of dark modules in a row as one rectangle', () => {
    const matrix = {
      size: 3,
      get: (row: number, col: number) => [1, 1, 0, 0, 0, 1, 1, 0, 1][row * 3 + col] ?? 0,
    };

    expect(darkRunsPath(matrix)).toBe('M0 0h2v1h-2zM2 1h1v1h-1zM0 2h1v1h-1zM2 2h1v1h-1z');
  });

  it('draws nothing for a matrix with no dark module', () => {
    expect(darkRunsPath({ size: 2, get: () => 0 })).toBe('');
  });
});

describe('qrDrawing — a check-in payload as a QR code', () => {
  const PAYLOAD =
    'RAKETA-CHECK-IN:1:3f2b8c1e-0000-4000-8000-000000000001:11111111-2222-4333-8444-555555555555:K7M2QX';

  it('encodes the payload at a version that holds it, with its finder patterns in the corners', () => {
    const drawing = qrDrawing(PAYLOAD);

    // A version's side is 17 + 4 × version, and a hundred characters need more than version 1's 21.
    expect((drawing.size - 17) % 4).toBe(0);
    expect(drawing.size).toBeGreaterThan(21);
    // The top-left finder's first row is seven dark modules: one run.
    expect(drawing.path.startsWith('M0 0h7v1h-7z')).toBe(true);
  });

  it('draws the same payload the same way every time', () => {
    expect(qrDrawing(PAYLOAD)).toEqual(qrDrawing(PAYLOAD));
  });
});
