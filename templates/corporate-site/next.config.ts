import type { NextConfig } from "next";
const config: NextConfig = {
  poweredByHeader: false,
  async headers() {
    return [{ source: "/:path*", headers: [
      { key: "Content-Security-Policy", value: "form-action 'none'; base-uri 'self'; object-src 'none'" },
    ] }];
  },
  images: { unoptimized: true },
  experimental: { cpus: 2 },
};
export default config;
