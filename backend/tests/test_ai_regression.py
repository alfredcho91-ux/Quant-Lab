import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

# Add backend to sys.path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(backend_path.parent))

from modules.ai_lab import service as ai_service
from config import settings

@pytest.fixture(autouse=True)
def clear_ai_response_cache():
    ai_service.AI_RESPONSE_CACHE.clear()
    yield
    ai_service.AI_RESPONSE_CACHE.clear()

def test_process_ai_research_uses_settings_key_when_no_key_provided():
    """
    Verify that process_ai_research uses settings.GEMINI_API_KEY 
    when api_key argument is None.
    """
    mock_settings_key = "AIza_mock_settings_key"
    mock_prompt = "Test prompt"
    
    # Mock settings.GEMINI_API_KEY
    with patch.object(settings, 'GEMINI_API_KEY', mock_settings_key):
        # Mock _call_gemini to avoid real API calls
        with patch('modules.ai_lab.service._call_gemini') as mock_call:
            mock_call.return_value = {
                "thought": "Mocked thought",
                "params": {"symbol": "BTCUSDT", "timeframe": "1h"},
                "error": None,
                "error_code": None
            }
            
            # Mock _run_conditional_probability_analysis to return None so it proceeds to _call_gemini
            with patch('modules.ai_lab.service._run_conditional_probability_analysis', return_value=None):
                # Mock _validate_gemini_key to return None (success)
                with patch('modules.ai_lab.service._validate_gemini_key', return_value=None):
                    
                    ai_service.process_ai_research(prompt=mock_prompt, api_key=None)
                    
                    # Verify _call_gemini was called with the key from settings
                    mock_call.assert_called_once()
                    args, kwargs = mock_call.call_args
                    assert kwargs['api_key'] == mock_settings_key

def test_process_ai_research_raises_error_when_both_keys_missing():
    """
    Verify that process_ai_research returns an error when both 
    api_key argument and settings.GEMINI_API_KEY are missing.
    """
    # Mock settings.GEMINI_API_KEY to be empty
    with patch.object(settings, 'GEMINI_API_KEY', ""):
        result = ai_service.process_ai_research(prompt="Test prompt", api_key=None)
        
        assert result.get("error") is not None
        assert ("API key is missing" in result["error"]) or ("API key is empty" in result["error"])
        assert result["error_code"] == ai_service.ERROR_CODE_API_KEY_INVALID
