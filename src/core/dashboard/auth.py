"""
Módulo de autenticación para el dashboard.
"""

import streamlit as st
from typing import Optional

from src.core.dashboard.dependency_injection import get_service_registry
from src.core.dashboard.services import AuthService
from src.core.dashboard.models import UserCredentials

def login_page():
    """
    Página de login del dashboard
    """
    st.title("🔐 Acceso al Dashboard")
    
    # Obtener servicio de autenticación
    auth_service = get_service_registry().get(AuthService)
    
    with st.form("login_form"):
        username = st.text_input("Email", placeholder="usuario@ejemplo.com")
        password = st.text_input("Contraseña", type="password")
        submit = st.form_submit_button("Iniciar Sesión")
        
        if submit:
            # Crear credenciales
            credentials = UserCredentials(email=username, password=password)
            
            # Intentar autenticar
            user = auth_service.login(credentials)
            
            if user:
                st.session_state.authenticated = True
                st.session_state.user = user.to_dict()
                
                # Usar condicional para manejar diferentes versiones de Streamlit
                if hasattr(st, 'rerun'):
                    st.rerun()
                else:
                    st.experimental_rerun()
            else:
                st.error("Credenciales inválidas. Intente nuevamente.")
    
    # Modo desarrollo - Bypass de autenticación
    if st.sidebar.checkbox("Modo Desarrollo", value=False):
        if st.sidebar.button("Login como Admin"):
            st.session_state.authenticated = True
            st.session_state.user = {
                "id": "dev-admin",
                "email": "admin@ejemplo.com",
                "role": "admin"
            }
            
            # Usar condicional para manejar diferentes versiones de Streamlit
            if hasattr(st, 'rerun'):
                st.rerun()
            else:
                st.experimental_rerun()

def authenticate_user() -> bool:
    """
    Verifica si el usuario está autenticado
    
    Returns:
        bool: True si el usuario está autenticado, False en caso contrario
    """
    # Verificar si la sesión tiene el indicador de autenticación
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    return st.session_state.authenticated

def get_current_user() -> Optional[dict]:
    """
    Obtiene el usuario actual
    
    Returns:
        Optional[dict]: Datos del usuario o None si no hay usuario autenticado
    """
    if 'user' in st.session_state and st.session_state.authenticated:
        return st.session_state.user
    return None

def has_role(required_role: str) -> bool:
    """
    Verifica si el usuario actual tiene el rol requerido
    
    Args:
        required_role: Rol requerido
        
    Returns:
        bool: True si el usuario tiene el rol requerido, False en caso contrario
    """
    user = get_current_user()
    if not user:
        return False
    
    if required_role == "user":
        return True
    elif required_role == "admin":
        return user.get("role") == "admin"
    
    return False

def logout_user() -> None:
    """Cierra la sesión del usuario actual"""
    # Obtener servicio de autenticación
    auth_service = get_service_registry().get(AuthService)
    
    user = get_current_user()
    if user:
        auth_service.logout(user["id"])
    
    # Limpiar sesión
    if "user" in st.session_state:
        del st.session_state.user
    
    st.session_state.authenticated = False
