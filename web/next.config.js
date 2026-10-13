/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "upload.wikimedia.org",
      },
      {
        protocol: "https",
        hostname: "**.wikipedia.org",
      },
      {
        protocol: "https",
        hostname: "**.wikimedia.org",
      },
    ],
  },
  async rewrites() {
    if (process.env.USE_LOCAL_API === "true") {
      return [
        {
          source: "/api/:path*",
          destination: "http://localhost:8000/api/:path*",
        },
      ];
    }
    return [];
  },
};

module.exports = nextConfig;
