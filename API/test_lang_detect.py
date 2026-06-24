import sys

sys.path.append("/Users/daoson/MyProject/MAT/API")
from services.language_detector_service import VietnameseDetector

detector = VietnameseDetector()
result = detector.is_vietnamese("xin chao huyndai")
print(result)
