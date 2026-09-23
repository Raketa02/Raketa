import { AppError } from './AppError';
import { liveLine } from './liveLine';

describe('what a row says about its read', () => {
  const draw = (count: number) => `${count} slots ticked`;

  it('draws the fact once it is in', () => {
    expect(liveLine({ data: 10, error: null }, draw)).toBe('10 slots ticked');
  });

  it('says nothing while the read is on its way', () => {
    expect(liveLine({ data: undefined, error: null }, draw)).toBeUndefined();
  });

  it('says the recovery once the read has failed, rather than going quiet', () => {
    const error = new AppError('server', 'terminal', 'test failure');
    expect(liveLine({ data: undefined, error }, draw)).toBe(
      'Something went wrong at our end. Try again later.',
    );
  });
});
