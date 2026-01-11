"""
Langfuse Client - Integration with Langfuse for AI observability.
"""
from typing import Optional, Dict, Any
from app.config.settings import settings

# Optional import for Langfuse
try:
    from langfuse import Langfuse
    from langfuse.decorators import langfuse_context, observe
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    Langfuse = None
    observe = lambda *args, **kwargs: lambda func: func  # No-op decorator


class LangfuseClient:
    """Client for Langfuse observability."""
    
    _client: Optional[Any] = None
    
    @classmethod
    def get_client(cls):
        """Get or create Langfuse client."""
        if not LANGFUSE_AVAILABLE:
            return None
        
        if cls._client is None:
            # Check if Langfuse keys are configured
            # In production, these would be in settings
            # For now, return None if not configured
            pass
        
        return cls._client
    
    @staticmethod
    def trace_run(
        run_id: str,
        agent_name: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Trace an AI run with Langfuse.
        
        Returns:
            Trace ID if successful, None otherwise
        """
        client = LangfuseClient.get_client()
        if not client:
            return None
        
        try:
            trace = client.trace(
                name=f"{agent_name}_run",
                id=run_id,
                metadata=metadata or {},
            )
            
            generation = trace.generation(
                name="agent_execution",
                model=agent_name,
                input=input_data,
                output=output_data,
            )
            
            return trace.id
        except Exception as e:
            print(f"Langfuse tracing error: {e}")
            return None
    
    @staticmethod
    def trace_generation(
        trace_id: str,
        name: str,
        model: str,
        input_data: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
    ):
        """Add a generation to an existing trace."""
        client = LangfuseClient.get_client()
        if not client:
            return
        
        try:
            trace = client.trace(id=trace_id)
            trace.generation(
                name=name,
                model=model,
                input=input_data,
                output=output_data,
            )
        except Exception:
            pass
