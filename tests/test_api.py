import requests
import time
from concurrent.futures import ThreadPoolExecutor
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# kubectl get svc -n production indexify -o jsonpath='{.status.loadBalancer.ingress[0].ip}'
EXTERNAL_IP = "135.234.208.173"  
API_ENDPOINT = f"http://{EXTERNAL_IP}:8900/graph/Extract_pages_tables_images_pdf_docling/run"
TEST_PDF = "https://arxiv.org/pdf/1706.03762"

def test_single_request():
    try:
        logger.info("Sending test request...")
        start = time.time()
        
        # Add timeout and explicit headers
        response = requests.post(
            API_ENDPOINT,
            json={"file": TEST_PDF},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        duration = time.time() - start
        logger.info(f"Response status: {response.status_code}")
        logger.info(f"Response content: {response.text[:200]}...")  # Show first 200 chars
        logger.info(f"Request took: {duration:.2f}s")
        return response.status_code
        
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        return 500

def load_test(requests=10, workers=5):
    logger.info(f"\nStarting load test with {requests} requests...")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        start = time.time()
        futures = [executor.submit(test_single_request) for _ in range(requests)]
        results = [f.result() for f in futures]
        total_time = time.time() - start
        
    success = sum(1 for code in results if code == 200)
    logger.info(f"\nLoad test results ({requests} requests):")
    logger.info(f"Success rate: {success/requests*100:.1f}%")
    logger.info(f"Total time: {total_time:.2f}s")
    logger.info(f"Requests/sec: {requests/total_time:.2f}")

if __name__ == "__main__":
    print("=== Starting API Tests ===")
    print("Testing single request:")
    test_single_request()
    
    print("\nStarting load test...")
    load_test(requests=10, workers=3)
    print("=== Tests Complete ===")
