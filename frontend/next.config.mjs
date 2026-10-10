/** @type {import('next').NextConfig} */
const nextConfig = {
  // The Docker runtime stage ships only .next/standalone (server.js + traced deps), not node_modules.
  output: "standalone",
};

export default nextConfig;
