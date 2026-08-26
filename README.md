# Auth Service

Sistema de autenticación y autorización completo: registro, login con JWT (access + refresh tokens), roles y permisos, rate limiting, recuperación de contraseña y un frontend simple para probarlo todo de forma visual.

Proyecto de portafolio centrado en seguridad backend real, más allá de un login básico.

## Arquitectura

```
Cliente (HTML/JS)
  │
  ▼
POST /auth/register ──────► Postgres (hash de contraseña con bcrypt)
POST /auth/login     ──────► verifica credenciales
                              │
                              ▼
                        Redis (rate limiting por IP)
                              │
                              ▼
                        genera access_token + refresh_token (JWT)

GET  /me                    ──► requiere access_token válido
POST /auth/refresh          ──► rota access_token + refresh_token
GET  /admin/users           ──► requiere rol 'admin'
POST /auth/forgot-password  ──► genera token de un solo uso (Postgres)
POST /auth/reset-password   ──► valida el token y cambia la contraseña
```

## Stack

- **API**: FastAPI
- **Validación**: Pydantic
- **Base de datos**: PostgreSQL + SQLAlchemy
- **Hashing de contraseñas**: passlib + bcrypt
- **Tokens**: JWT (python-jose)
- **Rate limiting**: Redis
- **Frontend**: HTML + JavaScript vanilla, servido como estáticos desde FastAPI
- **Infraestructura local**: Docker Compose

## Funcionalidades

- [x] Registro de usuarios con contraseñas hasheadas (bcrypt, nunca en texto plano)
- [x] Login con generación de access token y refresh token (JWT)
- [x] Endpoint protegido `/me` mediante `HTTPBearer`
- [x] Refresh de tokens con rotación (cada uso genera un par nuevo)
- [x] Distinción explícita entre tipos de token (`access` vs `refresh`), para que uno no pueda usarse en lugar del otro
- [x] Roles y permisos (RBAC) mediante una dependencia reutilizable (`require_role`)
- [x] Rate limiting en el login (Redis, por IP, con ventana temporal mediante TTL)
- [x] Recuperación de contraseña con token de un solo uso y expiración
- [x] Protección contra enumeración de usuarios (mismas respuestas exista o no la cuenta/email)
- [x] Frontend simple (HTML/JS) con manejo automático de expiración y refresco de tokens
- [ ] Envío real de emails (de momento el token de recuperación se imprime en el log del servidor)
- [ ] Login social (OAuth2 con Google/GitHub)
- [ ] Tests automatizados y pipeline de CI
- [ ] Lista negra de refresh tokens para revocación inmediata (logout real del lado del servidor)

## Cómo ejecutarlo en local

### Requisitos

- Python 3.11+
- Docker y Docker Compose

### 1. Clonar el repositorio

```bash
git clone https://github.com/narcisaducovschi/auth-service.git
cd auth-service
```

### 2. Crear el entorno virtual e instalar dependencias

```bash
python3 -m venv venv
source venv/bin/activate  # en Windows: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configurar las variables de entorno

```bash
cp .env.example .env
```

Genera una `SECRET_KEY` propia (no uses la de ejemplo):

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Pega el resultado en `.env`.

### 4. Levantar Postgres y Redis

```bash
docker-compose up -d
```

### 5. Arrancar la API

```bash
uvicorn app.main:app --reload
```

Disponible en `http://localhost:8000`, con documentación interactiva en `http://localhost:8000/docs`.

### 6. Probar con el frontend

```
http://localhost:8000/static/index.html
```

Desde ahí puedes registrarte, iniciar sesión, ver tu perfil, cerrar sesión y probar la recuperación de contraseña.

## Uso de la API

**Registro:**

```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

**Login:**

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

Devuelve `access_token`, `refresh_token` y `token_type`.

**Endpoint protegido:**

```bash
curl http://localhost:8000/me \
  -H "Authorization: Bearer TU_ACCESS_TOKEN"
```

**Renovar el access token:**

```bash
curl -X POST http://localhost:8000/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "TU_REFRESH_TOKEN"}'
```

**Recuperar contraseña:**

```bash
curl -X POST http://localhost:8000/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com"}'
```

El token de recuperación se imprime en la consola del servidor (marcado como `[DEV]`), ya que este proyecto no envía emails reales.

```bash
curl -X POST http://localhost:8000/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN_DEL_LOG", "new_password": "nuevacontraseña123"}'
```

## Estructura del proyecto

```
app/
├── main.py             # endpoints de la API
├── config.py            # configuración (variables de entorno)
├── database.py           # conexión a Postgres (SQLAlchemy)
├── models.py              # modelos: User, PasswordResetToken
├── schemas.py             # validación de entrada/salida (Pydantic)
├── security.py            # hashing de contraseñas y creación/verificación de JWT
├── dependencies.py         # get_current_user, require_role
├── crud.py                 # operaciones de base de datos
├── rate_limit.py            # límite de intentos de login (Redis)
└── static/                  # frontend (HTML, CSS, JS)
    ├── index.html
    ├── profile.html
    ├── style.css
    └── app.js
```

## Decisiones de diseño

- **El hashing de contraseñas es unidireccional**: nunca se guarda ni se puede recuperar la contraseña original, solo su hash (bcrypt, con salt único por contraseña incluido automáticamente).
- **Los JWT están firmados, no cifrados**: cualquiera puede leer su contenido, pero nadie puede modificarlo sin invalidar la firma. Por eso nunca se guarda información sensible dentro del payload.
- **Distinción de tipo dentro del propio token** (`type: "access"` / `"refresh"`): evita que un token pensado para un propósito se use en el endpoint equivocado, aunque ambos estén firmados con la misma clave.
- **Rotación de refresh tokens**: cada vez que se usa un refresh token se entrega uno nuevo, limitando la ventana de uso de un token robado.
- **Mismas respuestas exista o no el usuario/email**: tanto en login como en recuperación de contraseña, para no permitir que alguien enumere qué cuentas existen en el sistema probando muchas combinaciones.
- **Rate limiting con Redis y TTL**: se usa Redis por su velocidad y porque el TTL nativo resetea la ventana de intentos automáticamente, sin necesidad de procesos de limpieza propios.
- **Tokens de recuperación de contraseña como cadenas aleatorias en base de datos, no JWT**: al necesitar invalidarse tras un solo uso, un valor aleatorio verificado contra la base de datos es más apropiado que un JWT, que no se puede revocar individualmente sin infraestructura adicional.
- **Frontend en HTML/JS plano, sin framework**: el foco del proyecto es la autenticación en el backend; un frontend simple permite probar y demostrar el flujo completo (incluido el refresco automático de tokens) sin añadir complejidad de un framework de por medio.

## Limitaciones conocidas

- El envío de emails está simulado (el token de recuperación se imprime en el log del servidor).
- Los tokens se guardan en `localStorage` en el frontend; en un sistema de producción se suele preferir una cookie `httpOnly` para el refresh token, más resistente a ataques XSS.
- No hay revocación inmediata de refresh tokens ya emitidos (por ejemplo, ante un logout forzado desde el servidor); actualmente expiran solo por tiempo.

## Licencia

MIT