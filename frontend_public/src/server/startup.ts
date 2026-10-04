import 'server-only';

import { ConfigError, loadConfig } from './config';

export function refuseToStartWithoutConfig(): void {
  try {
    loadConfig();
  } catch (error) {
    if (!(error instanceof ConfigError)) throw error;
    console.error(error.message);
    process.exit(1);
  }
}
