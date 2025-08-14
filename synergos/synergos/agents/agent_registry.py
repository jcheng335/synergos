class AgentRegistry:
    """
    Registry for managing agent instances and types.
    Allows dynamic creation and retrieval of agents.
    """
    
    def __init__(self):
        self.agent_types = {}
        self.agent_instances = {}
    
    def register(self, agent_type, agent_class):
        """Register an agent class for a specific type"""
        self.agent_types[agent_type] = agent_class
    
    def get_agent(self, agent_type, agent_id=None, **kwargs):
        """
        Get or create an agent instance.
        If agent_id is provided, tries to retrieve existing instance.
        Otherwise, creates a new instance with the given kwargs.
        """
        if agent_type not in self.agent_types:
            raise ValueError(f"Agent type '{agent_type}' is not registered")
        
        # If agent_id is provided, try to get existing instance
        if agent_id and agent_id in self.agent_instances:
            return self.agent_instances[agent_id]
        
        # Create new instance
        agent_class = self.agent_types[agent_type]
        agent = agent_class(**kwargs)
        
        # If agent_id is provided, store the instance
        if agent_id:
            self.agent_instances[agent_id] = agent
        
        return agent
    
    def remove_agent(self, agent_id):
        """Remove an agent instance by ID"""
        if agent_id in self.agent_instances:
            del self.agent_instances[agent_id]
            return True
        return False
    
    def list_agent_types(self):
        """List all registered agent types"""
        return list(self.agent_types.keys())
    
    def list_agent_instances(self):
        """List all active agent instances"""
        return list(self.agent_instances.keys()) 