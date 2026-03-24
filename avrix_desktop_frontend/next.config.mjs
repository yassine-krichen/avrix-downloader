/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  // Ensure assets are loaded relative to the HTML file for Electron
  assetPrefix: '.',
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
}

export default nextConfig
