import unittest
import json
from unittest.mock import patch, MagicMock
from hermes.core.llm_provider import OllamaProvider

class TestProviderHealth(unittest.TestCase):
    def test_ollama_provider_diagnostics_message(self):
        provider = OllamaProvider(model="test-model", base_url="http://test-url:11434")
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.side_effect = Exception("Connection refused")
            
            with self.assertRaises(Exception) as cm:
                provider.completion("hello")
            
            err_msg = str(cm.exception)
            self.assertIn("Ollama API Error", err_msg)
            self.assertIn("base_url=http://test-url:11434", err_msg)
            self.assertIn("model=test-model", err_msg)
            self.assertIn("endpoint=http://test-url:11434/api/chat", err_msg)
            self.assertIn("diagnostics", err_msg)

    def test_ollama_health_check_format(self):
        provider = OllamaProvider(base_url="http://localhost:11434")
        
        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_response = MagicMock()
            mock_response.read.return_value = json.dumps({
                "models": [{"name": "qwen3:14b"}]
            }).encode('utf-8')
            mock_response.__enter__.return_value = mock_response
            mock_urlopen.return_value = mock_response
            
            health = provider.health_check()
            self.assertEqual(health["status"], "ok")
            self.assertEqual(health["data"]["models"][0]["name"], "qwen3:14b")

if __name__ == "__main__":
    unittest.main()
