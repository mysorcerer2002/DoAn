import withSerwistInit from "@serwist/next";

const withSerwist = withSerwistInit({
  swSrc: "src/app/sw.ts",
  swDest: "public/sw.js",
  disable: process.env.NODE_ENV === "development",
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    const backend = process.env.BACKEND_INTERNAL_URL || "http://backend:8000";
    return [
      { source: "/api/:path*", destination: `${backend}/:path*` },
    ];
  },
};

export default withSerwist(nextConfig);
