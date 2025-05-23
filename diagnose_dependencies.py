"""
Dependency Diagnostic Tool - Bot_Arbitraje2105
Verifies all dependencies and checks for conflicts
"""

import subprocess
import sys
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible"""
    print("[PYTHON] Checking Python version...")
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 9):
        print(f"[ERROR] Python {version.major}.{version.minor} detected. Python 3.9+ required!")
        return False
    print(f"[OK] Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_package_installed(package_name):
    """Check if a package is installed"""
    try:
        import importlib
        importlib.import_module(package_name.replace('-', '_'))
        return True
    except ImportError:
        return False

def get_installed_version(package_name):
    """Get installed version of a package"""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", package_name],
            capture_output=True,
            text=True
        )
        for line in result.stdout.splitlines():
            if line.startswith("Version:"):
                return line.split(":")[1].strip()
    except:
        pass
    return None

def check_critical_dependencies():
    """Check critical dependencies for the application"""
    print("\n[DEPENDENCIES] Checking critical dependencies...")
    
    critical_packages = {
        "fastapi": "0.112.0",
        "websockets": "12.0",
        "aiohttp": "3.9.0",
        "uvicorn": "0.25.0",
        "pydantic": "2.5.0",
        "python-binance": "1.0.19",
        "streamlit": "1.29.0"
    }
    
    all_good = True
    
    for package, min_version in critical_packages.items():
        installed = check_package_installed(package)
        if installed:
            version = get_installed_version(package)
            print(f"[OK] {package}: {version or 'Unknown version'}")
        else:
            print(f"[ERROR] {package}: Not installed (minimum: {min_version})")
            all_good = False
    
    return all_good

def check_import_errors():
    """Check for import errors in key modules"""
    print("\n[IMPORTS] Checking module imports...")
    
    modules_to_check = [
        ("FastAPI", "fastapi"),
        ("WebSockets", "websockets"),
        ("Binance Client", "binance"),
        ("Streamlit", "streamlit"),
        ("Uvicorn", "uvicorn"),
    ]
    
    all_good = True
    
    for name, module in modules_to_check:
        try:
            __import__(module)
            print(f"[OK] {name}: Import successful")
        except ImportError as e:
            print(f"[ERROR] {name}: Import failed - {e}")
            all_good = False
    
    # Check local modules
    print("\n[LOCAL] Checking local modules...")
    try:
        # Add src to path temporarily
        src_path = Path(__file__).parent
        sys.path.insert(0, str(src_path))
        
        # Try importing binance_websocket
        import binance_websocket
        print("[OK] binance_websocket: Import successful")
    except ImportError as e:
        print(f"[ERROR] binance_websocket: Import failed - {e}")
        all_good = False
    
    return all_good

def suggest_fixes():
    """Suggest fixes for common issues"""
    print("\n[FIXES] Suggested fixes:")
    print("1. Update all dependencies:")
    print("   python -m pip install -r requirements_optimized.txt")
    print("\n2. If import errors persist:")
    print("   - Use launch_production.py instead of production_server.py")
    print("   - Ensure you're in the correct directory")
    print("\n3. For version conflicts:")
    print("   - Create a fresh virtual environment")
    print("   - Install from requirements_optimized.txt")

def main():
    print("=" * 60)
    print("BOT ARBITRAJE 2105 - DEPENDENCY DIAGNOSTIC")
    print("=" * 60)
    
    # Check Python version
    if not check_python_version():
        return
    
    # Check critical dependencies
    deps_ok = check_critical_dependencies()
    
    # Check imports
    imports_ok = check_import_errors()
    
    # Overall status
    print("\n" + "=" * 60)
    if deps_ok and imports_ok:
        print("[SUCCESS] All checks passed! System ready.")
    else:
        print("[WARNING] Some issues detected.")
        suggest_fixes()
    print("=" * 60)

if __name__ == "__main__":
    main()
