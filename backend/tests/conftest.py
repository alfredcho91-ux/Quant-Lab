"""
pytest 설정 및 공통 픽스처
"""
import sys
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))
