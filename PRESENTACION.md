# Guía de Presentación - SE-PEAV
## Avance de Tesis II

**Duración:** 15-20 minutos

---

## Estructura de la Presentación

### 1. Introducción (2 minutos)

**Qué decir:**
> "SE-PEAV es un Sistema Edge de Predimensionamiento Estructural y Análisis de Vulnerabilidad para viviendas autoconstruidas en zonas sísmicas de Perú."

**Puntos clave:**
- Problema: Viviendas escalonadas construidas sin profesional técnico
- Contexto: País con alto riesgo sísmico
- Solución: Sistema automatizado de análisis estructural
- Tecnología: Dron DJI M4E + Celular con LiDAR + IA

---

### 2. Arquitectura del Sistema (3 minutos)

**Mostrar:** Diagrama de arquitectura en el README

**Explicar:**
```
Captura → API → Procesamiento → Análisis → Reporte

1. CAPTURA: Dron (exterior) + Celular LiDAR (interior)
2. API: FastAPI + PostgreSQL + MinIO
3. PROCESAMIENTO: COLMAP + 3DGS + YOLO
4. ANÁLISIS: Norma E.060 peruana
5. REPORTE: PDF con vulnerabilidades + Visor 3D
```

**Destacar:**
- Arquitectura de microservicios
- Escalable con Docker
- Pipeline asíncrono con Celery

---

### 3. Demo en Vivo (8 minutos)

**Ejecutar:** `.\demo.ps1`

**Script de demostración:**

1. **Verificar servicios** (30 seg)
   - Mostrar que todos los contenedores están corriendo
   - Explicar cada servicio (PostgreSQL, Redis, MinIO)

2. **Registro de usuario** (1 min)
   - Registrar nuevo usuario en vivo
   - Mostrar respuesta de la API

3. **Login** (1 min)
   - Autenticar usuario
   - Explicar JWT tokens

4. **Crear proyecto** (1 min)
   - Crear proyecto con datos realistas
   - Mostrar coordenadas GPS

5. **Crear inspección** (1 min)
   - Crear inspección de dron
   - Explicar tipos de captura

6. **Listar datos** (1 min)
   - Mostrar proyectos creados
   - Mostrar estado de inspección

7. **Endpoints disponibles** (1.5 min)
   - Mostrar tabla de endpoints
   - Explicar cada grupo (Auth, Projects, Inspections, Reports)

8. **Análisis E.060** (1 min)
   - Explicar verificaciones implementadas
   - Mostrar niveles de vulnerabilidad

---

### 4. Análisis E.060 (3 minutos)

**Qué decir:**
> "El sistema implementa el análisis según la norma peruana E.060 de albañilería."

**Verificaciones implementadas:**

| Verificación | Requisito | Por qué importa |
|--------------|-----------|-----------------|
| Espesor de muros | 15-25cm según pisos | Resistencia estructural |
| Confinamiento | Cada 4m máximo | Evitar colapso sísmico |
| Relación vano/muro | Máximo 0.6 | Estabilidad de muros |
| Refuerzo | 0.25% del área | Ductilidad |

**Niveles de vulnerabilidad:**
- 0-24: Bajo (aceptable)
- 25-49: Medio (monitorear)
- 50-74: Alto (reforzar)
- 75-100: Crítico (intervención inmediata)

---

### 5. Hoja de Ruta (2 minutos)

**Completado:**
- ✅ Backend API completo
- ✅ Infraestructura Docker
- ✅ Análisis E.060
- ✅ Pipeline de procesamiento
- ✅ Tests unitarios

**Próximos pasos:**
- ⏳ App Flutter con LiDAR Scanner
- ⏳ Visor Three.js
- ⏳ Integrar modelo YOLO
- ⏳ Deploy en producción

**Visión final:**
> "El usuario final podrá capturar imágenes de su vivienda desde su celular, el sistema analizará la estructura según la norma E.060, y generará un reporte con vulnerabilidades y recomendaciones, visualizado en 3D."

---

### 6. Preguntas y Respuestas (2 minutos)

**Preguntas frecuentes preparadas:**

**P: ¿Por qué usar dron y celular?**
> R: El dron captura la fachada y estructura exterior del edificio completo. El celular con LiDAR captura el interior con precisión milimétrica. Combinando ambos obtenemos un modelo 3D completo.

**P: ¿Qué pasa si no tengo dron?**
> R: El sistema funciona solo con capturas de celular. El dron es opcional pero mejora significativamente el análisis del exterior.

**P: ¿Qué tan preciso es el análisis?**
> R: El análisis E.060 implementa las verificaciones oficiales de la norma peruana. La precisión depende de la calidad de las capturas y el modelo YOLO entrenado.

**P: ¿Cuándo estará listo para producción?**
> R: El backend está listo. Faltan la app móvil y el visor 3D. Estimamos 2-3 meses más para un MVP completo.

---

## Preparación Pre-Demo

### Verificar antes de la presentación:

1. **Servicios Docker corriendo:**
   ```bash
   docker compose ps
   ```

2. **API accesible:**
   ```bash
   curl http://localhost:8000/health
   ```

3. **Swagger UI visible:**
   - Abrir http://localhost:8000/docs

4. **Script de demo listo:**
   - Verificar que `demo.ps1` existe
   - Ejecutar una vez antes de la presentación

### Si algo falla:

1. **API no responde:**
   ```bash
   docker compose restart backend
   ```

2. **Base de datos con problemas:**
   ```bash
   docker compose restart postgres
   ```

3. **Mostrar código como respaldo:**
   - `backend/app/api/v1/auth.py` - Autenticación
   - `backend/app/services/e060_analysis.py` - Análisis E.060
   - `backend/app/models/project.py` - Modelos de datos

---

## Archivos de Apoyo

| Archivo | Propósito |
|---------|-----------|
| `README.md` | Documentación completa + Estado del desarrollo |
| `demo.ps1` | Script de demostración en vivo |
| `docker-compose.yml` | Configuración de servicios |
| `backend/app/main.py` | Punto de entrada de la API |
| `backend/app/services/e060_analysis.py` | Análisis E.060 |

---

## Tips para la Presentación

1. **Habla claro y pausado** - No te apresures
2. **Muestra el código** - Los evaluadores quieren ver implementación
3. **Explica las decisiones técnicas** - ¿Por qué FastAPI? ¿Por qué Docker?
4. **Menciona las normas** - E.060, E.030 (cargas sísmicas)
5. **Ten ejemplos reales** - Direcciones, coordenadas de Lima
6. **Prepara respuestas** - Anticipa preguntas técnicas

---

## Contacto y Repositorio

- **GitHub:** https://github.com/tenk1u/SE_PEAV
- **API Docs:** http://localhost:8000/docs
- **MinIO Console:** http://localhost:9001

**¡Éxito en tu presentación!**
