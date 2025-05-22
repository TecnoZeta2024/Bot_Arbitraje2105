"""
Script principal para ejecutar los validadores de nodos n8n.
"""

import argparse
import sys
import os
from typing import Dict, Any, List, Optional

# Agregar directorio raíz al path para importar modules del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from src.utils.logger import get_logger

# Configurar logger
logger = get_logger("n8n_validador_main")

def validar_recomendacion():
    """Ejecuta el validador del nodo "Evaluar Recomendación IA"."""
    print("\nEjecutando validación de nodo 'Evaluar Recomendación IA'...")
    from n8n_validators.validar_recomendacion_ia import validar_recomendacion_ia
    return validar_recomendacion_ia()

def validar_decision():
    """Ejecuta el validador del nodo "Procesar Decisión Usuario"."""
    print("\nEjecutando validación de nodo 'Procesar Decisión Usuario'...")
    from n8n_validators.validar_decision_usuario import validar_decision_usuario
    return validar_decision_usuario()

def validar_supabase():
    """Ejecuta el validador de las tablas Supabase."""
    print("\nEjecutando validación de tablas Supabase...")
    from n8n_validators.validar_supabase import validar_tablas_supabase
    return validar_tablas_supabase()

def mostrar_menu():
    """Muestra el menú de opciones de validación."""
    print("\n" + "="*50)
    print("VALIDADOR DE NODOS N8N - BOT DE ARBITRAJE TRIANGULAR")
    print("="*50)
    print("1. Validar nodo 'Evaluar Recomendación IA'")
    print("2. Validar nodo 'Procesar Decisión Usuario'")
    print("3. Validar tablas Supabase")
    print("4. Ejecutar todas las validaciones")
    print("0. Salir")
    print("="*50)
    
    opcion = input("Seleccione una opción: ")
    return opcion

def main():
    """Función principal del validador."""
    while True:
        opcion = mostrar_menu()
        
        if opcion == "1":
            validar_recomendacion()
        elif opcion == "2":
            validar_decision()
        elif opcion == "3":
            validar_supabase()
        elif opcion == "4":
            validar_recomendacion()
            validar_decision()
            validar_supabase()
        elif opcion == "0":
            print("\nSaliendo del validador...")
            break
        else:
            print("\nOpción no válida. Inténtelo de nuevo.")
        
        input("\nPresione Enter para continuar...")

if __name__ == "__main__":
    # Configurar argumentos
    parser = argparse.ArgumentParser(description="Validador de nodos n8n")
    parser.add_argument("--all", action="store_true", help="Ejecuta todas las validaciones")
    parser.add_argument("--recomendacion", action="store_true", help="Valida nodo 'Evaluar Recomendación IA'")
    parser.add_argument("--decision", action="store_true", help="Valida nodo 'Procesar Decisión Usuario'")
    parser.add_argument("--supabase", action="store_true", help="Valida tablas Supabase")
    
    args = parser.parse_args()
    
    if len(sys.argv) > 1:
        # Si se proporcionaron argumentos, ejecutar validaciones específicas
        if args.all or (not args.recomendacion and not args.decision and not args.supabase):
            # Ejecutar todas las validaciones
            validar_recomendacion()
            validar_decision()
            validar_supabase()
        else:
            # Ejecutar validaciones específicas
            if args.recomendacion:
                validar_recomendacion()
            if args.decision:
                validar_decision()
            if args.supabase:
                validar_supabase()
    else:
        # Si no hay argumentos, mostrar menú interactivo
        main()
