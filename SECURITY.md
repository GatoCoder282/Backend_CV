# 🔐 GUÍA DE SEGURIDAD - Portfolio API

## CHECKLIST DE SEGURIDAD PRE-PRODUCCIÓN

### 1. Variables de Entorno
- [ ] `.env` está en `.gitignore` (nunca commitearlo)
- [ ] `SECRET_KEY` generado con `secrets.token_hex(32)` (mínimo 32 caracteres)
- [ ] `DATABASE_URL` apunta a PostgreSQL (NO SQLite en prod)
- [ ] Credenciales Cloudinary en variables de entorno (NO hardcodeadas)
- [ ] `ENVIRONMENT=prod` en configuración de producción

### 2. Base de Datos
- [ ] PostgreSQL versión 13+ en producción
- [ ] Migraciones aplicadas: `alembic upgrade head`
- [ ] Backups automáticos configurados
- [ ] Conexión segura (SSL/TLS si es remota)
- [ ] Índices creados en campos frecuentemente consultados

### 3. Autenticación & Autorización
- [ ] JWT tokens con expiración apropiada (30 min por defecto)
- [ ] Contraseñas hasheadas con Argon2 (no md5, no sha1)
- [ ] Validación de roles (ADMIN, SUPERADMIN) funcionando
- [ ] Headers Bearer token validados en endpoints protegidos
- [ ] Rate limiting implementado (opcional pero recomendado)

### 4. CORS y Dominios
```python
# ❌ MAL (desarrollo local)
allow_origins = ["*"]
allow_methods = ["*"]

# ✅ BIEN (producción)
allow_origins = ["https://tu-dominio.com"]
allow_methods = ["GET", "POST", "PUT", "DELETE"]
allow_headers = ["Content-Type", "Authorization"]
```

### 5. Headers de Seguridad
Los siguientes headers se envían automáticamente:
```
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### 6. HTTPS/TLS
- [ ] Certificado SSL válido (Let's Encrypt es gratis)
- [ ] Redirección HTTP → HTTPS
- [ ] Configurar en Nginx/Gunicorn

### 7. Validación de Entrada
- [ ] EmailStr valida emails automáticamente
- [ ] Lengths mínimos/máximos en campos
- [ ] Tipos validados con Pydantic
- [ ] SQL Injection protegido (SQLModel maneja esto)

### 8. Logging y Monitoreo
- [ ] Logs en JSON para mejor parseo
- [ ] Rotación de logs (no crecer indefinidamente)
- [ ] Errores 5xx registrados (Sentry, DataDog, etc.)
- [ ] Eventos críticos loguean (login, cambios de permisos)

### 9. Cloudinary
- [x] API Key y Secret en variables (ya implementado)
- [ ] Validación de tipos de archivo (imagen vs PDF)
- [ ] Límite tamaño de archivos
- [ ] Carpetas organizadas por usuario/tipo

### 10. Dependencias
- [ ] Todas las dependencias actualizadas
- [ ] Sin depedencias obsoletas
- [ ] Vulnerabilidades chequeadas: `pip install safety && safety check`

---

## COMANDOS ÚTILES

### Generar SECRET_KEY seguro
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Verificar vulnerabilidades en dependencias
```bash
pip install safety
safety check
```

### Ejecutar en producción (Gunicorn)
```bash
gunicorn \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile - \
  src.main:app
```

### Generar certificado SSL (Let's Encrypt)
```bash
# Usar en producción con Nginx
certbot certonly --standalone -d tu-dominio.com
```

---

## VULNERABILIDADES COMUNES (EVITAR)

| Vulnerabilidad | ¿Cómo evitarla? | Estado |
|---|---|---|
| SQL Injection | Usar ORM (SQLModel) ✅ | ✅ Implementado |
| CSRF | Validar tokens, CORS correcto | ✅ Implementado |
| XXS | No confiar en input del usuario | ✅ Pydantic valida |
| Contraseñas débiles | Argon2, min 6 caracteres | ✅ Implementado |
| JWT expiración | Token expiry: 30 min | ✅ Implementado |
| Información sensible en logs | Nunca loguear passwords | ✅ Implementado |
| Dependencias sin parchear | Actualizar regularmente | ⚠️ Revisar |
| API sin rate limit | Implementar rate limiting | ⚠️ Opcional |

---

## ROLES Y PERMISOS

```python
# ADMIN
- Crear/editar/eliminar su propio portfolio
- Ver su perfil

# SUPERADMIN  
- Acceso a todo (admin del sistema)
- Crear usuarios
- Cambiar roles

# PÚBLICO
- Ver perfiles públicos
- Ver portafolios
- NO editar nada sin autenticación
```

---

## TESTING DE SEGURIDAD

```bash
# Ejecutar todos los tests
pytest

# Tests solo de autenticación
pytest test/integration_test/test_authentication_flow.py -v

# Con cobertura de código
pytest --cov=src --cov-report=html
```

---

## DEPLOYMENT STEPS

1. **Clonar repo en servidor**
   ```bash
   git clone <repo> /app
   cd /app
   ```

2. **Crear entorno virtual**
   ```bash
   python3.12 -m venv venv
   source venv/bin/activate
   ```

3. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configurar variables**
   ```bash
   cp .env.example .env
   # Editar .env con valores REALES DE PRODUCCIÓN
   ```

5. **Preparar BD**
   ```bash
   alembic upgrade head
   ```

6. **Ejecutar con Gunicorn**
   ```bash
   gunicorn --workers 4 --bind 127.0.0.1:8000 src.main:app
   ```

7. **Configurar Nginx reverse proxy**
   ```nginx
   server {
       listen 443 ssl http2;
       server_name tu-dominio.com;
       
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
       
       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   
   # Redirect HTTP to HTTPS
   server {
       listen 80;
       server_name tu-dominio.com;
       return 301 https://$server_name$request_uri;
   }
   ```

---

## CONTACTO & SOPORTE

Para reportar vulnerabilidades:
- Email: [tu email]
- NO publicar vulnerabilidades en issues públicos

---

**Última actualización:** Febrero 2026  
**Versión:** 1.0.0
