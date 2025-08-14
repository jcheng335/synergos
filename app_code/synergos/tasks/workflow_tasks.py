import logging
import asyncio
from synergos.extensions import celery_app
from synergos.agents import orchestrator

# Set up logging
logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name='synergos.tasks.execute_workflow_task')
def execute_workflow_task(self, workflow_name, data, kwargs):
    """
    Celery task to execute a workflow asynchronously.
    
    Args:
        workflow_name (str): Name of the workflow to execute
        data (dict): Data required for the workflow
        kwargs (dict): Additional parameters for the workflow
        
    Returns:
        dict: The workflow results
    """
    try:
        logger.info(f"Executing workflow task: {workflow_name}")
        
        # Create event loop for async execution
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Execute workflow
        result = loop.run_until_complete(orchestrator.execute_workflow(workflow_name, data, **kwargs))
        
        logger.info(f"Workflow task completed: {workflow_name}")
        return result
        
    except Exception as e:
        logger.error(f"Error executing workflow task: {str(e)}")
        self.retry(exc=e, countdown=10, max_retries=3)
        raise
    finally:
        if 'loop' in locals():
            loop.close() 