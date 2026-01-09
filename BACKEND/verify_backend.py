import requests
import os

BASE_URL = "http://localhost:5000/api"
TEST_PDF_PATH = r"c:\Users\aruni\OneDrive\Desktop\ZYLO\lekl101.pdf"

def test_health():
    print("Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"Health check failed: {e}")

def test_pdf_upload():
    print("\nTesting PDF upload...")
    if not os.path.exists(TEST_PDF_PATH):
        print(f"Test PDF not found at {TEST_PDF_PATH}")
        return

    try:
        with open(TEST_PDF_PATH, 'rb') as f:
            files = {'pdf': f}
            response = requests.post(f"{BASE_URL}/pdf/upload-pdf", files=files)
            print(f"Upload: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Success: {data['success']}")
                print(f"PDF URL: {data['pdf_url']}")
                print(f"Total Sentences: {data['total_sentences']}")
                return data
            else:
                print(f"Error: {response.json()}")
    except Exception as e:
        print(f"Upload failed: {e}")

if __name__ == "__main__":
    print("Wait! Before running this, make sure the backend is running.")
    print("Start backend with: cd BACKEND && python app.py")
    # test_health()
    # test_pdf_upload()
