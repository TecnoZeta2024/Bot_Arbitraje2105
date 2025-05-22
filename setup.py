#!/usr/bin/env python3
"""
Setup Script for Advanced Personal Trading Platform
Bot_Arbitraje2105 v2.0

Este script configura automáticamente el entorno de desarrollo y producción.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import json
import platform


def print_banner():
    """Muestra el banner de setup."""
    banner = """
╔══════════════════════════════════════════════════════════════════════════════╗
║                                                                              ║
║                    🛠️  TRADING PLATFORM SETUP WIZARD 🛠️                    ║
║                            Bot_Arbitraje2105 v2.0                           ║
║                                                                              ║
║  This script will help you set up your advanced trading platform            ║
║                                                                              ║
╚══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_python_version():
    """Verifica la versión de Python."""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 9):
        print(f"❌ Error: Python 3.9 or higher is required")
        print(f"Current version: {sys.version}")
        print("Please upgrade Python and try again.")
        return False
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected")
    return True


def check_system_requirements():
    """Verifica los requisitos del sistema."""
    print("\n🔍 Checking system requirements...")
    
    # Verificar sistema operativo
    os_name = platform.system()
    print(f"Operating System: {os_name} {platform.release()}")
    
    # Verificar memoria RAM
    try:
        import psutil
        memory_gb = psutil.virtual_memory().total / (1024**3)
        print(f"Available RAM: {memory_gb:.1f} GB")
        
        if memory_gb < 4:
            print("⚠️  Warning: Low RAM detected. 8GB+ recommended for optimal performance.")
        else:
            print("✅ RAM requirements met")
    except ImportError:
        print("⚠️  Could not check RAM (psutil not installed)")
    
    # Verificar espacio en disco
    disk_usage = shutil.disk_usage(".")
    free_gb = disk_usage.free / (1024**3)
    print(f"Available disk space: {free_gb:.1f} GB")
    
    if free_gb < 5:
        print("⚠️  Warning: Low disk space. At least 5GB recommended.")
    else:
        print("✅ Disk space requirements met")
    
    return True


def create_virtual_environment():
    """Crea un entorno virtual Python."""
    print("\n🐍 Setting up Python virtual environment...")
    
    venv_path = Path(".venv")
    
    if venv_path.exists():
        response = input("Virtual environment already exists. Recreate? (y/N): ")
        if response.lower() == 'y':
            shutil.rmtree(venv_path)
        else:
            print("Using existing virtual environment")
            return True
    
    try:
        subprocess.run([sys.executable, "-m", "venv", ".venv"], check=True)
        print("✅ Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to create virtual environment: {e}")
        return False


def install_dependencies():
    """Instala las dependencias del proyecto."""
    print("\n📦 Installing dependencies...")
    
    # Determinar el comando pip correcto
    if platform.system() == "Windows":
        pip_cmd = [".venv\\Scripts\\pip"]
    else:
        pip_cmd = [".venv/bin/pip"]
    
    try:
        # Actualizar pip
        print("Upgrading pip...")
        subprocess.run(pip_cmd + ["install", "--upgrade", "pip"], check=True)
        
        # Instalar wheel para compilaciones más rápidas
        print("Installing wheel...")
        subprocess.run(pip_cmd + ["install", "wheel"], check=True)
        
        # Instalar dependencias principales
        print("Installing main dependencies...")
        subprocess.run(pip_cmd + ["install", "-r", "requirements.txt"], check=True)
        
        print("✅ Dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        print("You may need to install some dependencies manually:")
        print("- pip install ta-lib  # May require additional system libraries")
        return False


def setup_directories():
    """Crea los directorios necesarios."""
    print("\n📁 Setting up project directories...")
    
    directories = [
        "logs",
        "data",
        "cache",
        "backups",
        "reports",
        "tests/output",
        "docs"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")


def setup_environment_file():
    """Configura el archivo de entorno."""
    print("\n⚙️  Setting up environment configuration...")
    
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Keeping existing .env file")
            return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from template")
        print("📝 Please edit .env file with your configuration:")
        print("   - GEMINI_API_KEY: Your Google Gemini API key")
        print("   - TELEGRAM_BOT_TOKEN: Your Telegram bot token (optional)")
        print("   - BINANCE_API_KEY: Your Binance API key (for live trading)")
        return True
    else:
        print("❌ .env.example not found")
        return False


def setup_git_hooks():
    """Configura git hooks para desarrollo."""
    print("\n🔗 Setting up git hooks...")
    
    git_dir = Path(".git")
    if not git_dir.exists():
        print("⚠️  Git repository not initialized")
        return False
    
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)
    
    # Pre-commit hook para formatting
    pre_commit_hook = hooks_dir / "pre-commit"
    pre_commit_content = """#!/bin/sh
# Auto-format code before commit
black src/ --line-length 100
isort src/ --profile black
echo "Code formatted with black and isort"
"""
    
    with open(pre_commit_hook, "w") as f:
        f.write(pre_commit_content)
    
    pre_commit_hook.chmod(0o755)
    print("✅ Git pre-commit hook configured")
    
    return True


def verify_installation():
    """Verifica que la instalación sea correcta."""
    print("\n🔍 Verifying installation...")
    
    # Verificar importaciones críticas
    critical_imports = [
        "asyncio",
        "pandas", 
        "numpy",
        "aiohttp",
        "websockets",
        "google.generativeai"
    ]
    
    failed_imports = []
    
    for module in critical_imports:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError:
            print(f"❌ {module}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\n⚠️  Some modules failed to import: {failed_imports}")
        print("You may need to install them manually or check your virtual environment")
        return False
    
    print("\n✅ All critical modules imported successfully")
    return True


def create_test_script():
    """Crea un script de prueba."""
    print("\n🧪 Creating test script...")
    
    test_script = Path("test_setup.py")
    test_content = '''#!/usr/bin/env python3
"""
Quick test script to verify the setup
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_basic_imports():
    """Test basic imports."""
    print("Testing basic imports...")
    
    try:
        from domain.entities.market_data import MarketData
        from domain.entities.trading_signal import TradingSignal
        from infrastructure.container.di_container import DIContainer
        print("✅ Core modules imported successfully")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    return True

async def test_ai_connection():
    """Test AI connection."""
    print("Testing AI connection...")
    
    try:
        import google.generativeai as genai
        import os
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key or api_key == 'your_gemini_api_key_here':
            print("⚠️  GEMINI_API_KEY not configured")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        # Simple test
        response = model.generate_content("Hello, respond with 'AI test successful'")
        if "successful" in response.text.lower():
            print("✅ AI connection working")
            return True
        else:
            print("⚠️  AI response unexpected")
            return False
            
    except Exception as e:
        print(f"❌ AI test failed: {e}")
        return False

async def main():
    """Run all tests."""
    print("🧪 Running setup verification tests...\\n")
    
    tests = [
        test_basic_imports,
        test_ai_connection
    ]
    
    results = []
    for test in tests:
        result = await test()
        results.append(result)
        print()
    
    if all(results):
        print("🎉 All tests passed! Setup is complete.")
        print("\\nNext steps:")
        print("1. Edit .env file with your API keys")
        print("2. Run: cd src && python main_advanced.py")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")

if __name__ == "__main__":
    asyncio.run(main())
'''
    
    with open(test_script, "w") as f:
        f.write(test_content)
    
    test_script.chmod(0o755)
    print("✅ Test script created: test_setup.py")


def print_next_steps():
    """Muestra los próximos pasos."""
    print("\n" + "="*80)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*80)
    print("\n📋 Next Steps:")
    print("\n1. 🔑 Configure your API keys:")
    print("   - Edit .env file")
    print("   - Add your GEMINI_API_KEY (required)")
    print("   - Add TELEGRAM_BOT_TOKEN (optional)")
    print("   - Add BINANCE_API_KEY (for live trading)")
    
    print("\n2. 🧪 Test the setup:")
    print("   python test_setup.py")
    
    print("\n3. 🚀 Start the trading platform:")
    print("   cd src")
    print("   python main_advanced.py")
    
    print("\n4. 📚 Additional resources:")
    print("   - Documentation: docs/")
    print("   - Logs: logs/")
    print("   - Configuration: .env")
    
    print("\n⚠️  IMPORTANT:")
    print("   - Start with PAPER_TRADING=true")
    print("   - Test thoroughly before live trading")
    print("   - Monitor logs and performance")
    
    print("\n" + "="*80)


def main():
    """Función principal del setup."""
    print_banner()
    
    try:
        # Verificaciones previas
        if not check_python_version():
            return False
        
        check_system_requirements()
        
        # Setup paso a paso
        steps = [
            ("Creating virtual environment", create_virtual_environment),
            ("Installing dependencies", install_dependencies),
            ("Setting up directories", setup_directories),
            ("Configuring environment", setup_environment_file),
            ("Setting up git hooks", setup_git_hooks),
            ("Verifying installation", verify_installation),
            ("Creating test script", create_test_script)
        ]
        
        for description, func in steps:
            print(f"\n{'='*60}")
            print(f"Step: {description}")
            print(f"{'='*60}")
            
            if not func():
                print(f"❌ Failed: {description}")
                response = input("Continue anyway? (y/N): ")
                if response.lower() != 'y':
                    return False
        
        print_next_steps()
        return True
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        return False
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
