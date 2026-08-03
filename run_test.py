import os
import time
import subprocess
import socket
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def main():
    port = 8083
    server_process = None
    if not is_port_in_use(port):
        print(f"Starting local server on port {port}...")
        server_process = subprocess.Popen(
            ["python", "-m", "http.server", str(port)],
            cwd=r"c:\Users\au516150\OneDrive - Aarhus universitet\Desktop\Cellular_Snake",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        time.sleep(1.5)

    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1280,1024")
    
    print("Installing/Starting ChromeDriver...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        url = f"http://localhost:{port}/260703_Cellsnake.html"
        print(f"Loading {url}...")
        driver.get(url)
        time.sleep(2)
        
        # Inject JS to enable Dev Mode, toggle the fuzzer, and start the round
        print("Injecting devMode parameters & fast-forwarding...")
        driver.execute_script("""
            devMode = true;
            document.getElementById('devIndicator').style.display = 'block';
            fuzzActive = true;
            startRound();
        """)
        
        output_dir = r"c:\Users\au516150\OneDrive - Aarhus universitet\Desktop\Cellular_Snake\Test_screenshots"
        os.makedirs(output_dir, exist_ok=True)
        print(f"Screenshots will be saved to: {output_dir}")
        
        # Capture screenshots at 1.5-second intervals to cover the mitosis timeline
        for i in range(12):
            time.sleep(1.5)
            screenshot_path = os.path.join(output_dir, f"test_frame_{i+1}.png")
            driver.save_screenshot(screenshot_path)
            print(f"Captured frame {i+1}/12 to {screenshot_path}")
            
    finally:
        print("Cleaning up browser and server...")
        driver.quit()
        if server_process:
            server_process.terminate()

if __name__ == "__main__":
    main()
