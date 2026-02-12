
import time
import cv2
import numpy as np

def create_dummy_image():
    # create 1MB image
    img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
    _, buf = cv2.imencode('.jpg', img, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buf.tobytes()

def benchmark_decode(count=5):
    img_bytes = create_dummy_image()
    print(f"Benchmarking decoding of {count}  Full HD images...")
    
    start = time.time()
    for _ in range(count):
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    duration = time.time() - start
    print(f"Total time: {duration:.4f}s")
    print(f"Avg time per image: {duration/count*1000:.2f}ms")

if __name__ == "__main__":
    benchmark_decode()
