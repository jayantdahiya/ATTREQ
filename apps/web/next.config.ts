import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  images: {
    domains: ['localhost', 'dev-home-pi.online'], // Add backend domain for production
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/uploads/**',
      },
      {
        protocol: 'https',
        hostname: 'dev-home-pi.online',
        pathname: '/uploads/**',
      },
    ],
  }
}

export default nextConfig;
