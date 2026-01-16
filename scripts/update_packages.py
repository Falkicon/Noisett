#!/usr/bin/env python
"""Update all pip packages to latest versions."""
import subprocess
import sys

def update_packages():
    """Upgrade all installed pip packages."""
    print("🔄 Upgrading pip...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    
    print("\n🔄 Upgrading all packages...")
    # Get list of outdated packages
    result = subprocess.run(
        [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"],
        capture_output=True, text=True
    )
    
    import json
    try:
        outdated = json.loads(result.stdout)
    except json.JSONDecodeError:
        print("No outdated packages found!")
        return
    
    if not outdated:
        print("✅ All packages are up to date!")
        return
    
    print(f"Found {len(outdated)} outdated packages:")
    for pkg in outdated:
        print(f"  - {pkg['name']}: {pkg['version']} → {pkg['latest_version']}")
    
    # Upgrade each package
    for pkg in outdated:
        print(f"\n📦 Upgrading {pkg['name']}...")
        subprocess.run([
            sys.executable, "-m", "pip", "install", "--upgrade", pkg['name']
        ])
    
    print("\n✅ All packages updated!")

if __name__ == "__main__":
    update_packages()
