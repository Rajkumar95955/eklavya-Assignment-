"""
Base agent class with common functionality.
"""

from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Type
from pydantic import BaseModel, ValidationError
from openai import OpenAI
import json
import logging

from config import OPENAI_API_KEY, MODEL_NAME

logger = logging.getLogger(__name__)

InputT = TypeVar('InputT', bound=BaseModel)
OutputT = TypeVar('OutputT', bound=BaseModel)


class AgentError(Exception):
    """Custom exception for agent failures."""
    def __init__(self, message: str, agent_name: str, recoverable: bool = False):
        self.message = message
        self.agent_name = agent_name
        self.recoverable = recoverable
        super().__init__(f"[{agent_name}] {message}")


class BaseAgent(ABC, Generic[InputT, OutputT]):
    """
    Abstract base class for all agents.
    Provides common LLM interaction and schema validation.
    """
    
    name: str = "BaseAgent"
    output_schema: Type[OutputT] = None
    
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.model = MODEL_NAME
    
    @abstractmethod
    def _build_system_prompt(self) -> str:
        """Build the system prompt for this agent."""
        pass
    
    @abstractmethod
    def _build_user_prompt(self, input_data: InputT) -> str:
        """Build the user prompt from input data."""
        pass
    
    def _call_llm(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        """Make LLM API call and return raw response."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise AgentError(f"LLM call failed: {str(e)}", self.name, recoverable=True)
    
    def _parse_and_validate(self, raw_response: str) -> OutputT:
        """Parse JSON and validate against output schema."""
        try:
            parsed = json.loads(raw_response)
            return self.output_schema(**parsed)
        except json.JSONDecodeError as e:
            raise AgentError(f"Invalid JSON response: {str(e)}", self.name, recoverable=True)
        except ValidationError as e:
            raise AgentError(f"Schema validation failed: {str(e)}", self.name, recoverable=True)
    
    def run(self, input_data: InputT, max_retries: int = 1) -> OutputT:
        """
        Execute the agent with retry logic for schema validation.
        
        Args:
            input_data: Validated input data
            max_retries: Number of retries on validation failure
            
        Returns:
            Validated output matching output_schema
            
        Raises:
            AgentError: If all retries exhausted
        """
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(input_data)
        
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"[{self.name}] Attempt {attempt + 1}/{max_retries + 1}")
                raw_response = self._call_llm(system_prompt, user_prompt)
                result = self._parse_and_validate(raw_response)
                logger.info(f"[{self.name}] Success on attempt {attempt + 1}")
                return result
            except AgentError as e:
                last_error = e
                logger.warning(f"[{self.name}] Attempt {attempt + 1} failed: {e.message}")
                if not e.recoverable or attempt >= max_retries:
                    break
        
        raise AgentError(
            f"Failed after {max_retries + 1} attempts. Last error: {last_error.message}",
            self.name,
            recoverable=False
        )