/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static HTML export -> deployable to Firebase Hosting as static files.
  // All pages are client components that fetch from the API at runtime,
  // so no server runtime is needed.
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Emit /dashboard/index.html etc. so Firebase Hosting serves clean URLs.
  trailingSlash: true,
}

module.exports = nextConfig
