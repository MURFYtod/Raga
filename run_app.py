"""
Simple launcher for the Medical Appointment Scheduling AI Agent
"""
import subprocess
import sys
import os

def main():
    print("🚀 Starting Medical Appointment Scheduling AI Agent...")
    print("=" * 60)
    
    # Check if app.py exists
    if not os.path.exists("app.py"):
        print("❌ Error: app.py not found!")
        return
    
    # Check if .env file exists
    if not os.path.exists(".env"):
        print("⚠️  Warning: .env file not found. Please make sure your API keys are configured.")
    
    print("✅ Starting Streamlit application...")
    print("🌐 The app will open in your browser at: http://localhost:8501")
    print("📱 If it doesn't open automatically, copy the URL above to your browser")
    print("=" * 60)
    
    try:
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"], check=True)
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
