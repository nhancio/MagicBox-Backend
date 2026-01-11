# Agent Orchestration & Workflow Architecture

## Current Architecture

Currently, we have individual agents (PostAgent, ReelAgent, ImageAgent, VideoAgent) that work independently. Each agent:
- Has its own system prompt (loaded from JSON files)
- Uses Langfuse for observability
- Can be attached to projects
- Generates content independently

## Proposed: Agentic Workflow with Sub-Agents

### Why Orchestration?

1. **Better Quality**: Sub-agents can specialize in specific tasks (research, writing, editing, optimization)
2. **Modularity**: Each sub-agent handles one responsibility (Single Responsibility Principle)
3. **Reusability**: Sub-agents can be reused across different main agents
4. **Better Results**: Orchestration allows for multi-step refinement and validation
5. **Error Handling**: If one sub-agent fails, others can compensate or retry

### Proposed Architecture

```
Main Agent (e.g., PostAgent)
├── Research Sub-Agent
│   └── Gathers context, trends, audience insights
├── Content Generation Sub-Agent
│   └── Creates initial draft using Gemini 3 Pro
├── Optimization Sub-Agent
│   └── Optimizes for platform, tone, SEO
├── Validation Sub-Agent
│   └── Checks quality, brand guidelines, compliance
└── Finalization Sub-Agent
    └── Formats, adds hashtags, creates variations
```

### Implementation Approach

#### Option 1: Hierarchical Orchestration (Recommended)

```python
class PostAgent(BaseAgent):
    def execute(self, input_data):
        # Step 1: Research
        research_result = ResearchSubAgent(self.db, self.agent).execute({
            "topic": input_data["topic"],
            "platform": input_data["platform"]
        })
        
        # Step 2: Generate
        draft = ContentGenerationSubAgent(self.db, self.agent).execute({
            "topic": input_data["topic"],
            "research": research_result,
            "tone": input_data["tone"]
        })
        
        # Step 3: Optimize
        optimized = OptimizationSubAgent(self.db, self.agent).execute({
            "content": draft["content"],
            "platform": input_data["platform"]
        })
        
        # Step 4: Validate
        validated = ValidationSubAgent(self.db, self.agent).execute({
            "content": optimized["content"],
            "brand_guidelines": self.project.brand_guidelines
        })
        
        # Step 5: Finalize
        final = FinalizationSubAgent(self.db, self.agent).execute({
            "content": validated["content"],
            "hashtags": input_data.get("hashtags", True)
        })
        
        return final
```

#### Option 2: Workflow Engine (More Flexible)

Use a workflow engine like:
- **Temporal** (for complex workflows)
- **Prefect** (for data pipelines)
- **Custom workflow DSL** (lightweight)

```python
workflow = WorkflowBuilder()
    .add_step("research", ResearchSubAgent)
    .add_step("generate", ContentGenerationSubAgent, depends_on=["research"])
    .add_step("optimize", OptimizationSubAgent, depends_on=["generate"])
    .add_step("validate", ValidationSubAgent, depends_on=["optimize"])
    .add_step("finalize", FinalizationSubAgent, depends_on=["validate"])

result = workflow.execute(input_data)
```

### Sub-Agent Examples

#### 1. Research Sub-Agent
- **Purpose**: Gather context, trends, audience insights
- **Model**: Gemini 3 Pro (for research queries)
- **Output**: Research summary, key insights, trending topics

#### 2. Content Generation Sub-Agent
- **Purpose**: Create initial content draft
- **Model**: Gemini 3 Pro
- **Input**: Topic + Research + Brand Voice
- **Output**: Draft content

#### 3. Optimization Sub-Agent
- **Purpose**: Platform-specific optimization
- **Model**: Gemini 3 Pro
- **Input**: Draft + Platform requirements
- **Output**: Optimized content

#### 4. Validation Sub-Agent
- **Purpose**: Quality checks, brand compliance
- **Model**: Gemini 3 Pro (for validation)
- **Input**: Content + Brand Guidelines
- **Output**: Validated content + quality score

#### 5. Finalization Sub-Agent
- **Purpose**: Format, add hashtags, create variations
- **Model**: Gemini 3 Pro
- **Input**: Validated content
- **Output**: Final content + hashtags + variations

### Benefits of This Approach

1. **Better Quality**: Each step is specialized and optimized
2. **Easier Debugging**: Can inspect intermediate results
3. **Flexibility**: Can skip or modify steps based on requirements
4. **Scalability**: Sub-agents can be scaled independently
5. **Observability**: Each step can be traced separately in Langfuse

### Migration Path

1. **Phase 1**: Keep current agents, add orchestration layer
2. **Phase 2**: Extract sub-agents from main agents
3. **Phase 3**: Refactor main agents to use sub-agents
4. **Phase 4**: Add workflow engine for complex scenarios

### Recommendation

**Start with Option 1 (Hierarchical Orchestration)** because:
- Simpler to implement
- No external dependencies
- Easy to understand and maintain
- Can evolve to Option 2 later if needed

### Example: Enhanced Post Generation

```python
class PostAgent(BaseAgent):
    def execute(self, input_data):
        # Orchestrate sub-agents
        research = self._research(input_data)
        draft = self._generate(research, input_data)
        optimized = self._optimize(draft, input_data)
        validated = self._validate(optimized, input_data)
        final = self._finalize(validated, input_data)
        
        return final
    
    def _research(self, input_data):
        # Use ResearchSubAgent
        pass
    
    def _generate(self, research, input_data):
        # Use ContentGenerationSubAgent with Gemini 3 Pro
        pass
    
    def _optimize(self, draft, input_data):
        # Use OptimizationSubAgent
        pass
    
    def _validate(self, optimized, input_data):
        # Use ValidationSubAgent
        pass
    
    def _finalize(self, validated, input_data):
        # Use FinalizationSubAgent
        pass
```

This approach gives us:
- ✅ Better content quality
- ✅ Modular, testable code
- ✅ Easy to add new sub-agents
- ✅ Better observability
- ✅ Reusable components
