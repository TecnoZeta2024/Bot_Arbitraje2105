from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Configuración para JWT (estas deberían ser variables de entorno en un entorno de producción)
SECRET_KEY = "your-secret-key" # ¡Cambia esto por una clave segura y guárdala en un .env!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        if not isinstance(username, str):
            raise credentials_exception
        return username
    except JWTError:
        raise credentials_exception

# Función de ejemplo para verificar usuario (en un sistema real, esto vendría de una base de datos)
def authenticate_user(username: str, password: str):
    # Aquí iría la lógica para verificar el usuario en una base de datos
    # Por simplicidad, usaremos un usuario y contraseña fijos
    if username == "testuser" and password == "testpassword":
        return {"username": "testuser"}
    return None
