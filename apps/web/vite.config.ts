import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { VitePWA } from 'vite-plugin-pwa';
import path from 'node:path';

export default defineConfig({
    plugins: [
        react(),
        VitePWA({
            registerType: 'autoUpdate',
            includeAssets: ['favicon.svg'],
            manifest: {
                name: 'AI Dev Factory',
                short_name: 'ADF',
                description: 'Pilotez la construction de votre application depuis votre téléphone.',
                theme_color: '#0b0f1a',
                background_color: '#0b0f1a',
                display: 'standalone',
                start_url: '/',
                icons: [
                    { src: 'icon-192.png', sizes: '192x192', type: 'image/png' },
                    { src: 'icon-512.png', sizes: '512x512', type: 'image/png' },
                    {
                        src: 'icon-512.png',
                        sizes: '512x512',
                        type: 'image/png',
                        purpose: 'maskable',
                    },
                ],
            },
        }),
    ],
    resolve: {
        alias: { '@': path.resolve(__dirname, 'src') },
    },
    server: { port: 5173, host: true },
    test: {
        globals: true,
        environment: 'jsdom',
        setupFiles: './tests/setup.ts',
        include: ['tests/**/*.test.{ts,tsx}'],
        exclude: ['e2e/**', 'node_modules', 'dist'],
    },
});
