import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /*
   * The index lives in public/, which Vercel serves statically but does not
   * automatically trace into a route handler's bundle. Without this, loadIndex()
   * finds nothing in production and every answer falls back to ungrounded.
   */
  outputFileTracingIncludes: {
    "/api/**": ["./public/index/**"],
  },
};

export default nextConfig;
