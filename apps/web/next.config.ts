import type { NextConfig } from "next";
import { PHASE_PRODUCTION_BUILD } from "next/constants.js";
import { readConfig } from "./src/features/auth/server.ts";

const config: NextConfig = {
  transpilePackages: ["@coalsense/ui"],
  poweredByHeader: false,
  images: { unoptimized: true },
  experimental: { cpus: 2 }, // [SUPUESTO] acotar procesos de build en Windows y CI
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "Referrer-Policy", value: "no-referrer" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Permissions-Policy", value: "camera=(self), microphone=()" },
        ],
      },
    ];
  },
};
export default function nextConfig(phase: string): NextConfig {
  if (phase !== PHASE_PRODUCTION_BUILD) readConfig();
  return config;
}
