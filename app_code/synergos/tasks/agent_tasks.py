import logging
import asyncio
from synergos.extensions import celery_app
from synergos.agents import agent_registry

# Set up logging
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='synergos.tasks.process_agent_task')
def process_agent_task(self, agent_id, agent_class, data, kwargs):
    """
    Celery task to process an agent task asynchronously.
    
    Args:
        agent_id (str): ID of the agent or type of agent to use
        agent_class (str): Class name of the agent
        data (dict): Data to process
        kwargs (dict): Additional parameters for processing
        
    Returns:
        dict: The processing results
    """
    try:
        logger.info(f"Processing agent task: {agent_class} (ID: {agent_id})")
        
        # Create event loop for async execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Get agent from registry
        agent_type = agent_class.lower().replace('agent', '').replace('analysis', '')
        if not agent_type:
            agent_type = agent_id
            
        agent = agent_registry.get_agent(agent_type, agent_id)
        
        # Execute agent's process method
        result = loop.run_until_complete(agent.process(data, **kwargs))
        
        logger.info(f"Agent task completed: {agent_class} (ID: {agent_id})")
        return result
        
    except Exception as e:
        logger.error(f"Error processing agent task: {str(e)}")
        self.retry(exc=e, countdown=10, max_retries=3)
        raise
    finally:
        if 'loop' in locals():
            loop.close() 