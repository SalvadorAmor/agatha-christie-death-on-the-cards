import { defineConfig, configDefaults } from 'vitest/config';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  plugins: [react(), tailwindcss()],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/setupTests.ts',
    css: true,
    exclude: [...configDefaults.exclude, 'coverage'],
    // Instrumentar TODO el src aunque no se ejecute (esto evita % en 0 por archivos no tocados)
    all: true,

    coverage: {
      provider: 'v8',                 // más estable
      reporter: ['text', 'html'],     // consola + reporte navegable en coverage/index.html
      cleanOnRerun: true,             // limpia cobertura en cada rerun (watch/UI)
      all: true,                      // asegurar instrumentación total
      include: ['src/**/*.{ts,tsx}'], // solo código fuente
      exclude: [
        'src/**/*.test.*',
        'src/**/__tests__/**',
        'src/**/mocks/**',
        'src/main.tsx',
        'src/vite-env.d.ts'
      ],
    },
  },
});
