import type { NextConfig } from 'next';
const config: NextConfig = {
  experimental: { cpus: 2 }, poweredByHeader: false,
  webpack(config) {
    // Prisma TS source and offline NodeNext scripts retain .js specifiers.
    config.resolve.extensionAlias = { ...config.resolve.extensionAlias, '.js': ['.ts', '.tsx', '.js'] };
    return config;
  },
};
export default config;
