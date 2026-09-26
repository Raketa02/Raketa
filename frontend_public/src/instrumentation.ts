export async function register() {
  if (process.env.NEXT_RUNTIME === 'nodejs') {
    const { refuseToStartWithoutConfig } = await import('@/server/startup');
    refuseToStartWithoutConfig();
  }
}
