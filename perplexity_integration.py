"""
Perplexity AI Integration for Medical Appointment Scheduling AI Agent
"""
import httpx
import json
from typing import List, Dict, Any, Optional
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from config import Config

class PerplexityLLM:
    """Perplexity AI LLM integration using OpenAI-compatible API"""
    
    def __init__(self, api_key: str = None, model: str = "sonar-pro"):
        self.api_key = api_key or Config.PERPLEXITY_API_KEY
        self.model = model
        self.base_url = "https://api.perplexity.ai/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def is_configured(self) -> bool:
        """Check if Perplexity is properly configured"""
        return bool(self.api_key and self.api_key != "your_perplexity_api_key_here")
    
    def _convert_messages(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to Perplexity format"""
        perplexity_messages = []
        
        for message in messages:
            if isinstance(message, SystemMessage):
                perplexity_messages.append({
                    "role": "system",
                    "content": message.content
                })
            elif isinstance(message, HumanMessage):
                perplexity_messages.append({
                    "role": "user", 
                    "content": message.content
                })
            elif isinstance(message, AIMessage):
                perplexity_messages.append({
                    "role": "assistant",
                    "content": message.content
                })
        
        return perplexity_messages
    
    def invoke(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Invoke the Perplexity API with retry logic"""
        if not self.is_configured():
            raise ValueError("Perplexity API key not configured")
        
        perplexity_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": perplexity_messages,
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.1),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": False
        }
        
        # Retry logic for connection issues
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                with httpx.Client(timeout=60.0) as client:  # Increased timeout
                    response = client.post(
                        self.base_url,
                        headers=self.headers,
                        json=payload,
                        timeout=60.0
                    )
                    
                    if response.status_code != 200:
                        error_detail = response.text
                        if attempt < max_retries - 1:
                            print(f"Perplexity API error (attempt {attempt + 1}): {response.status_code} - {error_detail}")
                            import time
                            time.sleep(retry_delay * (attempt + 1))  # Exponential backoff
                            continue
                        raise Exception(f"Perplexity API error: {response.status_code} - {error_detail}")
                    
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    return AIMessage(content=content)
                    
            except httpx.ConnectError as e:
                if attempt < max_retries - 1:
                    print(f"Connection error (attempt {attempt + 1}): {e}")
                    import time
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise Exception(f"Perplexity API connection error: {e}")
            except httpx.TimeoutException as e:
                if attempt < max_retries - 1:
                    print(f"Timeout error (attempt {attempt + 1}): {e}")
                    import time
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise Exception(f"Perplexity API timeout error: {e}")
            except httpx.HTTPError as e:
                if attempt < max_retries - 1:
                    print(f"HTTP error (attempt {attempt + 1}): {e}")
                    import time
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise Exception(f"Perplexity API HTTP error: {e}")
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"General error (attempt {attempt + 1}): {e}")
                    import time
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise Exception(f"Error calling Perplexity API: {e}")
        
        raise Exception("Perplexity API failed after all retry attempts")
    
    def stream(self, messages: List[BaseMessage], **kwargs):
        """Stream responses from Perplexity API"""
        if not self.is_configured():
            raise ValueError("Perplexity API key not configured")
        
        perplexity_messages = self._convert_messages(messages)
        
        payload = {
            "model": self.model,
            "messages": perplexity_messages,
            "max_tokens": kwargs.get("max_tokens", 1000),
            "temperature": kwargs.get("temperature", 0.1),
            "top_p": kwargs.get("top_p", 1.0),
            "stream": True
        }
        
        try:
            with httpx.stream(
                "POST",
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                
                for line in response.iter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data.strip() == "[DONE]":
                            break
                        
                        try:
                            chunk = json.loads(data)
                            if "choices" in chunk and len(chunk["choices"]) > 0:
                                delta = chunk["choices"][0].get("delta", {})
                                if "content" in delta:
                                    yield delta["content"]
                        except json.JSONDecodeError:
                            continue
                            
        except httpx.HTTPError as e:
            raise Exception(f"Perplexity API streaming error: {e}")
        except Exception as e:
            raise Exception(f"Error streaming from Perplexity API: {e}")

# Example usage
if __name__ == "__main__":
    # Test Perplexity integration
    perplexity = PerplexityLLM()
    
    if perplexity.is_configured():
        print("✅ Perplexity API configured successfully")
        
        # Test a simple conversation
        messages = [
            SystemMessage(content="You are a helpful medical appointment scheduling assistant."),
            HumanMessage(content="Hello, I'd like to schedule an appointment.")
        ]
        
        try:
            response = perplexity.invoke(messages)
            print(f"Response: {response.content}")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("❌ Perplexity API not configured")
