import unittest
from unittest.mock import patch, MagicMock
from src.tools.code_executor import CodeExecutorTool

class TestCodeExecutorTool(unittest.TestCase):
    def setUp(self):
        self.code_executor = CodeExecutorTool(timeout=5, max_output_size=5000)
        
    def test_execute_code_placeholder(self):
        """Test the placeholder implementation"""
        code = "print('Hello, world!')"
        language = "python"
        
        result = self.code_executor.execute_code(code, language)
        
        # Check that the placeholder response contains expected elements
        self.assertIn("Python", result)  # Should mention the language name
        self.assertIn("CODE:", result)   # Should show the code
        self.assertIn(code, result)      # Should include the code
        self.assertIn("SIMULATED OUTPUT:", result)  # Should mention simulated output
    
    def test_execute_unsupported_language(self):
        """Test executing code in an unsupported language"""
        code = "main() { printf('Hello, world!'); }"
        language = "unsupported_language"
        
        result = self.code_executor.execute_code(code, language)
        
        # Should return an error message for unsupported language
        self.assertIn("Error", result)
        self.assertIn("not supported", result)
    
    def test_supported_languages(self):
        """Test getting the list of supported languages"""
        languages = self.code_executor.get_supported_languages()
        
        # Check that common languages are supported
        self.assertIn("python", languages)
        self.assertIn("javascript", languages)
        self.assertIn("bash", languages)
        self.assertIn("sql", languages)
    
    def test_language_info(self):
        """Test getting information about a language"""
        python_info = self.code_executor.get_language_info("python")
        
        # Check that we get detailed information
        self.assertEqual(python_info["name"], "Python")
        self.assertIn("version", python_info)
        self.assertIn("file_extension", python_info)
        self.assertIn("compiler", python_info)
        
        # Check case insensitivity
        python_upper = self.code_executor.get_language_info("PYTHON")
        self.assertEqual(python_info, python_upper)
        
        # Check unsupported language
        unsupported = self.code_executor.get_language_info("unsupported_language")
        self.assertIsNone(unsupported)
    
    def test_execute_javascript(self):
        """Test executing JavaScript code"""
        code = "console.log('Hello, JavaScript!');"
        language = "javascript"
        
        result = self.code_executor.execute_code(code, language)
        
        # Check JavaScript-specific elements
        self.assertIn("JavaScript", result)
        self.assertIn("Node.js", result)
    
    def test_execute_markdown(self):
        """Test rendering Markdown"""
        markdown = "# Hello Markdown\n\nThis is a test."
        language = "markdown"
        
        result = self.code_executor.execute_code(markdown, language)
        
        # Check Markdown-specific elements
        self.assertIn("Markdown", result)
        self.assertIn("Rendered", result)
        self.assertIn(str(len(markdown)), result)  # Should mention length
    
    def test_sandbox_availability(self):
        """Test checking sandbox availability"""
        # The current implementation always returns False as it's a placeholder
        self.assertFalse(self.code_executor._is_sandbox_available())

if __name__ == '__main__':
    unittest.main()