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
        
        response = requests.post(
            API_ENDPOINT,
            json={"file": TEST_PDF},
            timeout=30,
            headers={"Content-Type": "application/json"}
        )
        
        duration = time.time() - start
        logger.info(f"Response status: {response.status_code}")
        
        # Add proper assertions
        assert response.status_code == 200, "Expected 200 OK response"
        assert "invocation_id" in response.json(), "Missing invocation ID in response"
        
        logger.info(f"Request took: {duration:.2f}s")
        return  # Explicit return None
        
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        pytest.fail(f"Test failed: {str(e)}")

def load_test(requests=10, workers=5):
    logger.info(f"\nStarting load test with {requests} requests...")
    with ThreadPoolExecutor(max_workers=workers) as executor:
        start = time.time()
        futures = []
        for _ in range(requests):
            futures.append(executor.submit(test_single_request))
        
        results = []
        for future in futures:
            try:
                results.append(future.result(timeout=45))
            except TimeoutError:
                logger.error("Request timed out")
                results.append(504)

        total_time = time.time() - start
        
    success = sum(1 for code in results if code == 200)
    assert success/requests > 0.8, "Success rate below 80%"

if __name__ == "__main__":
    print("=== Starting API Tests ===")
    print("Testing single request:")
    test_single_request()
    
    print("\nStarting load test...")
    load_test(requests=10, workers=3)
    print("=== Tests Complete ===")
