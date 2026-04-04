import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Only proxy API in local development
  async rewrites() {
    return process.env.NEXT_PUBLIC_API_URL
      ? [] // In production, frontend calls the backend URL directly
      : [
          {
            source: "/api/:path*",
            destination: "http://localhost:8000/:path*",
          },
        ];
  },
};

export default nextConfig;
