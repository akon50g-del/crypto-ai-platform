/** @type {import('next').NextConfig} */
// BUILD_TARGET=mobile produces a static export (out/) for Capacitor/Android.
// Default (web) keeps the normal server build for Docker/Vercel.
const mobile = process.env.BUILD_TARGET === 'mobile';
const nextConfig = {
  reactStrictMode: true,
  ...(mobile ? { output: 'export', images: { unoptimized: true }, trailingSlash: true } : {}),
};
export default nextConfig;
