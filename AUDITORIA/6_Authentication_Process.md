# Proceso de Autenticación - Bot_Arbitraje2105

## Visión General del Sistema de Autenticación

El Bot_Arbitraje2105 implementa un sistema de autenticación y autorización basado en estándares modernos de seguridad, utilizando JSON Web Tokens (JWT) y mecanismos de hashing seguros. El sistema está diseñado para proporcionar acceso seguro tanto a las interfaces de usuario como a las APIs, con diferentes niveles de permisos según el rol del usuario.

## Arquitectura de Autenticación

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Capa Cliente   │     │   Capa API      │     │  Capa Dominio   │
│                 │     │                 │     │                 │
│  - Dashboard    │     │  - Validación   │     │  - Servicios    │
│  - API Clients  │ ──> │  - Middleware   │ ──> │    Protegidos   │
│  - CLI Tools    │     │  - Rate Limiting│     │  - Operaciones  │
│                 │     │                 │     │    Seguras      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                        │                       │
        ▼                        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Autenticación │     │  Autorización   │     │   Auditoría     │
│                 │     │                 │     │                 │
│  - Login        │     │  - Permisos     │     │  - Logging      │
│  - Registro     │     │  - Roles        │     │  - Trazabilidad │
│  - Tokens       │     │  - Políticas    │     │  - Alertas      │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Flujo de Autenticación

### 1. Registro de Usuario

El sistema permite la creación de nuevas cuentas de usuario con diferentes roles.

**Proceso:**
1. Usuario proporciona credenciales (email, contraseña, información personal)
2. Sistema valida formato y unicidad del email
3. Contraseña se hashea utilizando bcrypt con salt aleatorio
4. Se crea registro de usuario con rol predeterminado
5. Se envía email de confirmación (opcional)

**Implementación inferida:**
```python
# Servicio de Autenticación
async def register_user(self, email: str, password: str, user_data: Dict[str, Any]) -> User:
    """Registra un nuevo usuario en el sistema"""
    # Validar email y contraseña
    if not self._validate_email(email):
        raise ValueError("Invalid email format")
    
    if await self.user_repository.exists_by_email(email):
        raise ValueError("Email already registered")
    
    # Validar complejidad de contraseña
    if not self._validate_password_strength(password):
        raise ValueError("Password does not meet security requirements")
    
    # Generar hash de contraseña
    password_hash = self.password_hasher.hash(password)
    
    # Crear usuario con rol predeterminado
    user = User(
        user_id=str(uuid.uuid4()),
        email=email,
        password_hash=password_hash,
        role=UserRole.VIEWER,  # Rol predeterminado
        created_at=datetime.utcnow(),
        **user_data
    )
    
    # Persistir usuario
    await self.user_repository.save(user)
    
    # Enviar email de confirmación
    await self.notification_service.send_registration_email(user)
    
    return user
```

### 2. Inicio de Sesión

Proceso para autenticar usuarios existentes y emitir tokens de acceso.

**Proceso:**
1. Usuario proporciona credenciales (email, contraseña)
2. Sistema verifica existencia del email
3. Se compara el hash de la contraseña proporcionada con el almacenado
4. Si coincide, se genera un JWT con payload que incluye:
   - ID de usuario
   - Rol
   - Tiempo de emisión
   - Tiempo de expiración
5. Se devuelve el token al cliente

**Implementación inferida:**
```python
# Servicio de Autenticación
async def login(self, email: str, password: str) -> Dict[str, str]:
    """Autentica un usuario y devuelve tokens JWT"""
    # Buscar usuario por email
    user = await self.user_repository.find_by_email(email)
    if not user:
        raise AuthenticationError("Invalid credentials")
    
    # Verificar contraseña
    if not self.password_hasher.verify(password, user.password_hash):
        # Registrar intento fallido
        await self._log_failed_login_attempt(email)
        raise AuthenticationError("Invalid credentials")
    
    # Generar token JWT
    access_token = self._create_access_token(user)
    refresh_token = self._create_refresh_token(user)
    
    # Registrar login exitoso
    await self._log_successful_login(user)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

def _create_access_token(self, user: User) -> str:
    """Crea un token JWT de acceso"""
    expiration = datetime.utcnow() + timedelta(minutes=30)  # 30 min
    
    payload = {
        "sub": str(user.user_id),
        "email": user.email,
        "role": user.role.value,
        "exp": expiration,
        "iat": datetime.utcnow()
    }
    
    # Firmar con clave secreta
    return jwt.encode(payload, self.jwt_secret_key, algorithm="HS256")
```

### 3. Verificación de Token

Proceso para validar tokens en cada solicitud a endpoints protegidos.

**Proceso:**
1. Cliente incluye token en encabezado de autorización
2. Middleware extrae y valida el token
3. Se verifica firma, expiración y validez del token
4. Se extrae información del usuario y rol
5. Se adjunta contexto de seguridad a la solicitud

**Implementación inferida:**
```python
# Middleware de Autenticación
async def authenticate(self, request: Request, call_next):
    """Middleware para validar tokens JWT"""
    # Rutas públicas que no requieren autenticación
    if request.url.path in self.public_paths:
        return await call_next(request)
    
    # Extraer token del encabezado
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return JSONResponse(
            status_code=401,
            content={"detail": "Not authenticated"}
        )
    
    token = auth_header.split(" ")[1]
    
    try:
        # Verificar token
        payload = jwt.decode(
            token, 
            self.jwt_secret_key, 
            algorithms=["HS256"]
        )
        
        # Extraer información del usuario
        user_id = payload.get("sub")
        role = payload.get("role")
        
        # Crear contexto de seguridad
        security_context = {
            "user_id": user_id,
            "role": role,
            "authenticated": True
        }
        
        # Adjuntar contexto a la solicitud
        request.state.security_context = security_context
        
        # Continuar con la solicitud
        return await call_next(request)
        
    except jwt.ExpiredSignatureError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Token expired"}
        )
    except jwt.InvalidTokenError:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid token"}
        )
```

### 4. Renovación de Token

Mecanismo para renovar tokens de acceso sin requerir re-autenticación.

**Proceso:**
1. Cliente utiliza token de actualización (refresh token)
2. Sistema valida el refresh token
3. Se emite un nuevo token de acceso
4. Opcionalmente, se emite un nuevo refresh token

**Implementación inferida:**
```python
# Servicio de Autenticación
async def refresh_token(self, refresh_token: str) -> Dict[str, str]:
    """Renueva un token de acceso usando un refresh token"""
    try:
        # Verificar refresh token
        payload = jwt.decode(
            refresh_token, 
            self.jwt_refresh_secret, 
            algorithms=["HS256"]
        )
        
        # Extraer ID de usuario
        user_id = payload.get("sub")
        
        # Verificar que el usuario existe y está activo
        user = await self.user_repository.find_by_id(user_id)
        if not user or not user.is_active:
            raise AuthenticationError("Invalid refresh token")
        
        # Generar nuevo token de acceso
        new_access_token = self._create_access_token(user)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
        
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Refresh token expired")
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid refresh token")
```

### 5. Cierre de Sesión

Proceso para invalidar tokens activos.

**Proceso:**
1. Cliente envía solicitud de cierre de sesión
2. Token actual se agrega a una lista de revocación
3. Se invalidan sesiones activas del usuario

**Implementación inferida:**
```python
# Servicio de Autenticación
async def logout(self, token: str) -> None:
    """Cierra la sesión del usuario invalidando su token"""
    try:
        # Decodificar token sin verificar expiración
        payload = jwt.decode(
            token, 
            self.jwt_secret_key, 
            algorithms=["HS256"],
            options={"verify_exp": False}
        )
        
        # Extraer información relevante
        token_jti = payload.get("jti", "")
        user_id = payload.get("sub", "")
        
        # Agregar a lista de revocación
        await self.token_blacklist.add(token_jti, user_id)
        
        # Registrar cierre de sesión
        await self._log_logout(user_id)
        
    except jwt.InvalidTokenError:
        # Si el token ya es inválido, no hacer nada
        pass
```

## Sistema de Autorización

### 1. Modelo de Roles y Permisos

El sistema implementa un modelo basado en roles (RBAC) con permisos granulares.

**Roles Principales:**
- **ADMIN**: Acceso completo a todas las funcionalidades
- **TRADER**: Puede ejecutar operaciones y gestionar estrategias
- **ANALYST**: Puede ver datos y análisis pero no ejecutar operaciones
- **VIEWER**: Solo acceso de lectura a dashboards y reportes

**Implementación inferida:**
```python
# Enumeración de Roles
class UserRole(Enum):
    ADMIN = "ADMIN"
    TRADER = "TRADER"
    ANALYST = "ANALYST"
    VIEWER = "VIEWER"

# Permisos por Rol
ROLE_PERMISSIONS = {
    UserRole.ADMIN: {
        "user:create", "user:read", "user:update", "user:delete",
        "trade:create", "trade:read", "trade:update", "trade:cancel",
        "strategy:create", "strategy:read", "strategy:update", "strategy:delete",
        "system:configure", "system:read", "system:update",
        "report:create", "report:read", "report:export"
    },
    UserRole.TRADER: {
        "trade:create", "trade:read", "trade:update", "trade:cancel",
        "strategy:read", "strategy:update",
        "system:read",
        "report:read", "report:export"
    },
    UserRole.ANALYST: {
        "trade:read",
        "strategy:read",
        "system:read",
        "report:create", "report:read", "report:export"
    },
    UserRole.VIEWER: {
        "trade:read",
        "strategy:read",
        "system:read",
        "report:read"
    }
}
```

### 2. Verificación de Permisos

Mecanismo para validar que un usuario tiene los permisos necesarios para una operación.

**Proceso:**
1. Se extrae el rol del contexto de seguridad
2. Se verifica si el rol tiene el permiso requerido
3. Se permite o deniega la operación

**Implementación inferida:**
```python
# Decorador de Autorización
def require_permission(permission: str):
    """Decorador para verificar permisos en endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if not request:
                raise ValueError("Cannot find request object")
            
            # Obtener contexto de seguridad
            security_context = getattr(request.state, "security_context", None)
            if not security_context:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Not authenticated"}
                )
            
            # Verificar rol y permisos
            role = security_context.get("role")
            user_permissions = ROLE_PERMISSIONS.get(UserRole(role), set())
            
            if permission not in user_permissions:
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Permission denied"}
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 3. Endpoints Protegidos

Aplicación de autenticación y autorización a endpoints específicos.

**Ejemplo de uso:**
```python
# Endpoint protegido
@router.post("/api/trades")
@require_permission("trade:create")
async def create_trade(trade_data: TradeCreate, request: Request):
    """Crea una nueva operación de trading"""
    user_id = request.state.security_context["user_id"]
    
    # Crear operación
    trade = await trade_service.create_trade(trade_data, user_id)
    
    return {
        "status": "success",
        "data": trade
    }
```

## Seguridad y Protección

### 1. Almacenamiento Seguro de Credenciales

**Mecanismos implementados:**
- Hashing de contraseñas con bcrypt y salt único
- No almacenamiento de contraseñas en texto plano
- Protección de claves API con cifrado

### 2. Protección contra Ataques Comunes

**Medidas implementadas:**
- Rate limiting para prevenir ataques de fuerza bruta
- Validación de entradas para prevenir inyección
- Tokens con tiempo de expiración para limitar ventana de vulnerabilidad
- Rotación de secretos

### 3. Auditoría y Logging

**Características:**
- Registro de todos los intentos de autenticación (exitosos y fallidos)
- Trazabilidad de acciones críticas
- Alertas para actividad sospechosa
- Retención de logs para cumplimiento regulatorio

## Integración con Supabase

El sistema parece aprovechar Supabase para algunos aspectos de autenticación y gestión de usuarios.

**Características utilizadas:**
- Tablas PostgreSQL para almacenamiento de usuarios
- Posible uso de funcionalidades de autenticación de Supabase
- Row Level Security (RLS) para control de acceso a nivel de datos

## Problemas y Recomendaciones

## Problema: Implementación parcial del sistema de autenticación, origen: análisis de código ##
#Solución: Completar la implementación del sistema de autenticación, asegurando que todos los endpoints estén protegidos adecuadamente y que se implementen todas las funcionalidades (registro, login, refresh, logout) #

## Problema: Falta de gestión de sesiones, origen: ausencia de código relacionado ##
#Solución: Implementar un sistema de gestión de sesiones que permita control de sesiones activas, cierre forzado y limitación de sesiones concurrentes por usuario #

## Problema: Ausencia de autenticación de dos factores (2FA), origen: análisis de código ##
#Solución: Implementar 2FA utilizando TOTP (Time-based One-Time Password) o envío de códigos por email/SMS para operaciones críticas y acceso de administradores #

## Problema: Posible exposición de endpoints sensibles, origen: enhanced_api_server.py ##
#Solución: Revisar todos los endpoints y asegurar que estén protegidos con los middlewares de autenticación y decoradores de autorización adecuados, especialmente los endpoints de operaciones de trading y configuración del sistema #
