# Fase 15: Lighthouse CI

Lighthouse CI audita automáticamente la calidad del frontend construido sin consultar producción. El job `lighthouse` depende de `frontend-quality`, vuelve a instalar y construir el frontend en un runner limpio, inicia temporalmente Vite Preview en `127.0.0.1:4173` y analiza la ruta pública `/login`.

## Métricas y umbrales

La auditoría utiliza el perfil desktop y exige mínimos académicos alcanzables:

- Performance: 65%.
- Accessibility: 80%.
- Best Practices: 80%.
- SEO: 80%.

Estos valores funcionan como línea base: detectan regresiones importantes sin imponer puntajes irreales a una SPA académica. Deben elevarse gradualmente cuando se optimicen recursos, experiencia accesible y metadatos.

## Ejecución local

Desde `frontend`:

```powershell
npm ci
npm run lint
npm run build
npm run lighthouse
```

`npm run lighthouse` administra el servidor temporal configurado en `lighthouserc.json`. Los archivos generados quedan en `frontend/lighthouse-reports` y no se versionan.

## GitHub Actions

El workflow ejecuta Lighthouse únicamente contra el build local del runner. Al finalizar, publica `frontend/lighthouse-reports` como artifact `lighthouse-reports` durante 14 días, incluso si una métrica no alcanza el umbral. No usa Railway, Netlify, bases de datos, S3 ni URLs de producción, y no realiza despliegues.

Los resultados locales obtenidos durante la implementación se documentan en el informe de la fase; GitHub Actions vuelve a calcularlos en cada ejecución porque pueden variar ligeramente según el entorno.

## Resultado local de referencia

La auditoría de la pantalla `/login` sobre el build local obtuvo Performance 94%, Accessibility 100%, Best Practices 100% y SEO 82%. Las cuatro categorías superaron sus umbrales; estos valores son una referencia y pueden variar ligeramente en los runners de CI.
