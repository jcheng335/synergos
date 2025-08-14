import uuid
import logging
from abc import ABC, abstractmethod
# Remove direct openai import if only using the patched client
# import openai 
from synergos.extensions import celery_app

# Import the patched client getter function
# Assuming openai_client_fix.py is in the root directory relative to where the app runs
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from openai_client_fix import get_patched_client

# Set up logging
logger = logging.getLogger(__name__)

class AgentBase(ABC):
    """
    Base class for all agents in the system.
    Provides common functionality and defines the interface.
    """
    
    def __init__(self, name=None, model="gpt-3.5-turbo", **kwargs):
        """
        Initialize a new agent.
        
        Args:
            name (str): Optional name for the agent
            model (str): LLM model to use for this agent
            **kwargs: Additional agent-specific parameters
        """
        self.id = str(uuid.uuid4())
        self.name = name or f"{self.__class__.__name__}_{self.id[:8]}"
        self.model = model
        self.state = {}
        self.history = []
        self.config = kwargs
        
        # Get the client during initialization if needed elsewhere, or get it in _call_llm
        # self.client = get_patched_client() 
        # if not self.client:
        #    logger.error(f"Agent {self.name} failed to get OpenAI client during initialization.")
            # Handle error appropriately - maybe raise an exception?

        logger.info(f"Agent {self.name} (ID: {self.id}) initialized")
    
    @abstractmethod
    async def process(self, data, **kwargs):
        """
        Process data and return results.
        This is the main method for agent functionality.
        
        Args:
            data: The data to process
            **kwargs: Additional parameters for processing
            
        Returns:
            dict: The processing results
        """
        pass
    
    def process_async(self, data, **kwargs):
        """
        Process data asynchronously as a Celery task.
        
        Args:
            data: The data to process
            **kwargs: Additional parameters for processing
            
        Returns:
            AsyncResult: Celery task result
        """
        from synergos.tasks.agent_tasks import process_agent_task
        return process_agent_task.delay(self.id, self.__class__.__name__, data, kwargs)
    
    def _call_llm(self, messages, **kwargs):
        """
        Make a call to the LLM using the patched client.
        
        Args:
            messages (list): List of message dictionaries for the chat
            **kwargs: Additional parameters for the API call
            
        Returns:
            dict: LLM response
        """
        client = get_patched_client() # Get the patched client here
        if not client:
            logger.error(f"Agent {self.name} failed to get OpenAI client in _call_llm. Ensure client is initialized properly in app.")
            raise RuntimeError("Failed to get OpenAI client for LLM call")
            
        try:
            kwargs.setdefault("model", self.model)
            # Use the obtained patched client
            # client = openai.OpenAI() # REMOVED
            response = client.chat.completions.create(
                messages=messages,
                **kwargs
            )
            # Make sure the response structure is correct for OpenAI v1+
            # Assuming response structure is like response.choices[0].message.content
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content
            else:
                logger.error(f"Unexpected LLM response structure: {response}")
                raise ValueError("Unexpected LLM response structure")

        except Exception as e:
            # Log the specific type of exception and message
            logger.error(f"Error calling LLM ({type(e).__name__}): {str(e)}")
            # Re-raise the exception to be handled upstream
            raise
    
    def update_state(self, key, value):
        """Update the agent's state"""
        self.state[key] = value
        
    def get_state(self, key, default=None):
        """Get a value from the agent's state"""
        return self.state.get(key, default)
    
    def add_to_history(self, entry):
        """Add an entry to the agent's history"""
        self.history.append(entry)
    
    def get_history(self):
        """Get the agent's history"""
        return self.history
    
    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} id={self.id}>" 