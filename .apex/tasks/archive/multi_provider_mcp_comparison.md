# Multi-Provider LLM Agent with MCP Tools: Comprehensive Comparison

**Research Date:** October 23, 2025
**Context:** Building a trading strategy creation agent that works with Claude, GPT-4, and Gemini using MCP tools (yfinance, FRED, Composer)

---

## Executive Summary

**Recommended Approach:** **MCP Python SDK + Custom Multi-Provider Wrapper** (Option 5)

**Rationale:**
- MCP SDK is the canonical way to connect to MCP servers (yfinance, FRED, Composer)
- Custom wrapper provides clean abstraction over LLM provider differences (100-200 lines)
- LiteLLM doesn't directly support MCP clients (it's for LLM routing, not MCP tool management)
- LangChain adds unnecessary complexity for this use case
- Full control, minimal dependencies, production-ready

---

## Critical Finding: MCP Integration Architecture

**Key Insight:** MCP is a **tool protocol**, not an LLM provider abstraction. The architecture is:

```
┌─────────────────────────────────────────────────────┐
│                 Your Agent Code                     │
├─────────────────────────────────────────────────────┤
│  ┌────────────────┐        ┌──────────────────┐    │
│  │  MCP Client    │        │  LLM Provider    │    │
│  │  (Tools)       │        │  (Reasoning)     │    │
│  ├────────────────┤        ├──────────────────┤    │
│  │ - yfinance MCP │        │ - Claude         │    │
│  │ - FRED MCP     │◄──────►│ - GPT-4          │    │
│  │ - Composer MCP │        │ - Gemini         │    │
│  └────────────────┘        └──────────────────┘    │
└─────────────────────────────────────────────────────┘
         │                           │
         ▼                           ▼
   MCP Servers                   LLM APIs
```

**What this means:**
- MCP SDK connects to MCP servers and retrieves tools
- MCP SDK is provider-agnostic (doesn't care which LLM you use)
- You need a separate abstraction for LLM provider switching
- Tool definitions must be converted from MCP format to provider-specific formats

---

## Detailed Comparison

### Option 1: LiteLLM

**Description:** Unified API wrapper for 100+ LLM providers

#### MCP Tool Support
❌ **Does NOT directly support MCP client connections**

LiteLLM focuses on:
- LLM API routing (unified interface for OpenAI, Anthropic, Google, etc.)
- Tool calling format normalization (converts between provider formats)
- MCP Gateway (v1.65.0+) for exposing MCP tools via HTTP proxy

**How it works with MCP:**
- LiteLLM Proxy can act as an MCP Gateway (server-side)
- Client-side: You connect to MCP servers separately
- LiteLLM normalizes tool calling formats for LLM requests
- **You still need MCP SDK** to connect to MCP servers

#### Multi-Provider Support
✅ **Excellent** - Drop-in replacement for OpenAI SDK
```python
from litellm import completion

response = completion(
    model="anthropic/claude-sonnet-4-5",  # or "gpt-4o", "gemini/gemini-2.0-flash"
    messages=[{"role": "user", "content": "Hello"}],
    tools=[...]  # Automatically converts to provider format
)
```

#### Tool Calling Normalization
✅ **Automatic** - Handles provider format differences transparently

**Provider-specific formats handled:**
- Claude: `input_schema` → `parameters`
- OpenAI: `parameters` (native)
- Gemini: Native format or OpenAI-compatible

#### Setup Complexity
🟡 **Medium**
- Installation: `pip install litellm anthropic openai google-generativeai`
- Still need MCP SDK separately: `pip install mcp`
- Configuration for LiteLLM Proxy (if using gateway mode)

#### Code Simplicity
✅ **Very Simple** - Single API for all providers
```python
# One interface for all providers
response = completion(
    model=provider_model_string,
    messages=messages,
    tools=tools  # LiteLLM handles format conversion
)
```

#### Production Ready
✅ **Mature** - Used in production by thousands of companies
- Active development
- Comprehensive error handling
- Retry/fallback logic built-in
- Cost tracking and rate limiting

#### Community Support
✅ **Excellent**
- 14k+ GitHub stars
- Extensive documentation
- Active Discord community

#### Pros
- ✅ Simplest multi-provider switching
- ✅ Automatic tool format conversion
- ✅ Built-in retry, fallback, cost tracking
- ✅ Can use MCP Gateway for server-side MCP hosting
- ✅ Production-ready with observability

#### Cons
- ❌ Doesn't connect to MCP servers directly (need MCP SDK separately)
- ❌ Extra dependency (though lightweight)
- ❌ MCP Gateway requires proxy setup (optional feature)

#### Verdict for Your Use Case
**🟡 Partial Fit** - Great for LLM provider abstraction, but you still need MCP SDK for tool management. Recommended if you combine:
- **LiteLLM** for LLM provider switching
- **MCP SDK** for connecting to MCP servers
- **Custom glue code** to bridge the two (~50 lines)

---

### Option 2: Direct API Calls + Custom Abstraction

**Description:** Write your own wrapper for each provider's native API

#### MCP Tool Support
⚠️ **Manual** - You implement everything

Required implementation:
1. Connect to MCP servers via MCP SDK
2. Retrieve tool definitions
3. Convert MCP format to each provider's format
4. Handle tool calling responses
5. Execute tools via MCP SDK
6. Convert results to provider format

#### Multi-Provider Support
🟡 **Full Control** - Implement exactly what you need

Example structure:
```python
class LLMProvider(ABC):
    @abstractmethod
    def chat(self, messages, tools):
        pass

    @abstractmethod
    def format_tools(self, mcp_tools):
        pass

    @abstractmethod
    def extract_tool_calls(self, response):
        pass

class ClaudeProvider(LLMProvider):
    def format_tools(self, mcp_tools):
        # Convert MCP tools to Claude's input_schema format
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema  # Claude uses input_schema
            }
            for tool in mcp_tools
        ]

class OpenAIProvider(LLMProvider):
    def format_tools(self, mcp_tools):
        # Convert MCP tools to OpenAI's parameters format
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema  # OpenAI uses parameters
                }
            }
            for tool in mcp_tools
        ]

class GeminiProvider(LLMProvider):
    def format_tools(self, mcp_tools):
        # Convert to Gemini's FunctionDeclaration format
        from google.generativeai.types import FunctionDeclaration, Tool
        return [
            Tool(function_declarations=[
                FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema
                )
                for tool in mcp_tools
            ])
        ]
```

#### Tool Calling Normalization
⚠️ **Manual** - You implement all format conversions

**Format differences you must handle:**

| Aspect | Claude | OpenAI | Gemini |
|--------|--------|--------|--------|
| Tool schema key | `input_schema` | `parameters` | `parameters` |
| Tool wrapper | Direct array | `{"type": "function", "function": {...}}` | `Tool(function_declarations=[...])` |
| Response format | `tool_use` blocks | `tool_calls` array with IDs | `function_call` parts |
| Result format | `tool_result` blocks | `role: "tool"` with `tool_call_id` | `Part.from_function_response()` |
| Error handling | `"is_error": true` | HTTP errors | Custom exceptions |

#### Setup Complexity
🟢 **Low** - Minimal dependencies
```bash
pip install anthropic openai google-generativeai mcp
```

#### Code Simplicity
🔴 **High Maintenance** - 300-500 lines for full implementation
- Provider-specific API clients
- Format conversion logic
- Error handling per provider
- Tool execution routing

#### Production Ready
🟡 **Depends on Your Implementation**
- Full control over error handling
- No external framework dependencies
- Debugging is straightforward (no magic)
- But you own all the maintenance

#### Community Support
❌ **None** - You're on your own
- No shared codebase
- Can reference official docs for each provider
- MCP SDK docs for tool management

#### Pros
- ✅ Full control over every detail
- ✅ Minimal dependencies
- ✅ No framework lock-in
- ✅ Easy to debug (no abstractions)
- ✅ Learn provider APIs deeply

#### Cons
- ❌ Most code to write (300-500 lines)
- ❌ Maintenance burden (handle breaking changes)
- ❌ Manual format conversion for each provider
- ❌ No built-in retry/fallback logic
- ❌ You implement observability

#### Verdict for Your Use Case
**🔴 Not Recommended** - Too much boilerplate for first-time agent builder. Better options available.

---

### Option 3: LangChain with Multi-Provider

**Description:** Comprehensive framework for building LLM applications

#### MCP Tool Support
✅ **Official Adapters** (March 2025)

LangChain provides `langchain-mcp-adapters`:
```python
from langchain_mcp_adapters import MultiServerMCPClient

# Connect to MCP servers
mcp_client = MultiServerMCPClient({
    "yfinance": {
        "url": "http://localhost:8000/mcp",
        "transport": "streamable_http"
    },
    "fred": {
        "command": "npx",
        "args": ["-y", "@stefanoamorelli/fred-mcp-server"],
        "transport": "stdio"
    }
})

# Get LangChain-compatible tools
tools = await mcp_client.get_tools()
```

**How it works:**
- `MultiServerMCPClient` connects to multiple MCP servers
- Converts MCP tools to LangChain `Tool` objects
- Handles tool execution automatically
- Prefixes tool names with `mcp-{server_name}-` to avoid conflicts

#### Multi-Provider Support
✅ **Built-in** - Supports 100+ LLM providers

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

# Choose your provider
llm = ChatAnthropic(model="claude-sonnet-4-5")
# OR
llm = ChatOpenAI(model="gpt-4o")
# OR
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Use with MCP tools
from langgraph.prebuilt import create_react_agent

agent = create_react_agent(llm, tools)
result = await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})
```

#### Tool Calling Normalization
✅ **Automatic** - LangChain handles provider differences

LangChain's chat models normalize:
- Tool schema formats
- Response parsing
- Tool result formatting

#### Setup Complexity
🔴 **High** - Many dependencies
```bash
pip install langchain langchain-core langchain-mcp-adapters \
  langchain-anthropic langchain-openai langchain-google-genai \
  langgraph
```

**Configuration complexity:**
- MCP server configuration file (JSON)
- LangChain model initialization
- Agent creation and state management

#### Code Simplicity
🟡 **Medium** - Abstractions help, but learning curve

**Simple agent example (~50 lines):**
```python
from langchain_mcp_adapters import MultiServerMCPClient
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

# 1. Connect to MCP servers
mcp_client = MultiServerMCPClient(config)
tools = await mcp_client.get_tools()

# 2. Create agent
llm = ChatAnthropic(model="claude-sonnet-4-5")
agent = create_react_agent(llm, tools)

# 3. Run
result = await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})
```

**Complex workflow example (100-200 lines):**
- Custom StateGraph for fine-grained control
- Multiple tool nodes
- Conditional routing
- Memory management

#### Production Ready
✅ **Mature** - Battle-tested framework
- Used by thousands of companies
- LangSmith for observability
- Built-in retry and error handling
- Active development

**⚠️ Deprecation Warning:**
- MCP documentation will be updated with LangGraph v1.0 (October 2025)
- API may change

#### Community Support
✅ **Excellent**
- 100k+ GitHub stars (LangChain)
- Extensive documentation
- Active Discord community
- Many tutorials and examples

#### Pros
- ✅ Official MCP adapters
- ✅ Multi-provider support built-in
- ✅ High-level abstractions (create_react_agent)
- ✅ Production-ready with observability (LangSmith)
- ✅ Rich ecosystem (memory, callbacks, etc.)
- ✅ Handles tool name conflicts automatically

#### Cons
- ❌ Heavy framework (many dependencies)
- ❌ Steep learning curve
- ❌ Abstractions can be confusing to debug
- ❌ Overkill for simple agents
- ❌ API deprecation risk (MCP adapters are new)
- ❌ Framework lock-in

#### Verdict for Your Use Case
**🟡 Viable but Overkill** - LangChain is powerful but adds complexity you don't need. Good if:
- You plan to use LangChain's ecosystem (memory, callbacks, LangSmith)
- You want high-level abstractions like `create_react_agent`
- You're willing to learn the framework

**Not recommended if:**
- First-time agent builder
- Want minimal dependencies
- Prefer full control over agent loop

---

### Option 4: OpenRouter / Portkey (API Gateways)

**Description:** Proxy-based multi-provider LLM access

#### MCP Tool Support

**OpenRouter:**
❌ **Not an MCP client** - OpenRouter is an LLM routing service
- Provides unified API for 200+ LLM models
- **Does not connect to MCP servers**
- Can use MCP servers indirectly (you connect to MCP, OpenRouter handles LLM routing)

**Portkey:**
🟡 **Building MCP Gateway** (In Development)
- Portkey announced MCP Gateway support (2025)
- Acts as centralized control plane for context-aware workflows
- Features planned:
  - Access control for MCP tools
  - Audit logging
  - End-to-end tracing
  - Cost attribution

**Status:** Early development, not production-ready for MCP yet

#### Multi-Provider Support

**OpenRouter:**
✅ **Excellent** - 200+ models via single API
```python
from openai import OpenAI

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY
)

response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4-5",  # or "openai/gpt-4o", "google/gemini-2.0-flash"
    messages=[...]
)
```

**Portkey:**
✅ **Good** - Unified API for major providers
```python
from portkey_ai import Portkey

client = Portkey(
    api_key=PORTKEY_API_KEY,
    virtual_key=VIRTUAL_KEY  # Provider-specific
)

response = client.chat.completions.create(
    model="claude-sonnet-4-5",
    messages=[...]
)
```

#### Tool Calling Normalization

**OpenRouter:**
✅ **Uses OpenAI format** - All models use OpenAI's tool calling format
- Consistent interface across providers
- Less flexible than native APIs

**Portkey:**
✅ **Provider-aware** - Handles format differences
- Normalizes tool calling
- Adds observability layer

#### Setup Complexity
🟢 **Low** - Just API keys

**OpenRouter:**
```bash
pip install openai
export OPENROUTER_API_KEY=...
```

**Portkey:**
```bash
pip install portkey-ai
export PORTKEY_API_KEY=...
```

**For MCP:**
You still need `pip install mcp` to connect to MCP servers

#### Code Simplicity
✅ **Very Simple** - Similar to OpenAI SDK

**Architecture:**
```python
# 1. Connect to MCP servers (separate)
from mcp import ClientSession
mcp_tools = await mcp_client.list_tools()

# 2. Use OpenRouter/Portkey for LLM
from openai import OpenAI
client = OpenAI(base_url="https://openrouter.ai/api/v1", ...)

# 3. Bridge MCP tools to LLM format (you implement)
tools = convert_mcp_to_openai_format(mcp_tools)

response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4-5",
    messages=messages,
    tools=tools
)
```

#### Production Ready

**OpenRouter:**
✅ **Production-ready**
- Stable service
- Rate limiting
- Cost tracking
- Fallback support

**Portkey:**
✅ **Production-ready** (for LLM routing)
⚠️ **MCP Gateway in development**

#### Community Support

**OpenRouter:**
✅ **Good**
- Active community
- Documentation
- Discord support

**Portkey:**
✅ **Good**
- Enterprise-focused
- Comprehensive docs
- Slack support

#### Cost and Complexity

**OpenRouter:**
- 💰 **Cost:** Per-token pricing (markup on provider rates)
- 🔧 **Complexity:** Low - just HTTP proxy

**Portkey:**
- 💰 **Cost:** Subscription ($99-$999/mo) or pay-as-you-go
- 🔧 **Complexity:** Medium - more features, more config

#### Pros
- ✅ Simple multi-provider switching
- ✅ Built-in observability
- ✅ Cost tracking
- ✅ Rate limiting and fallbacks
- ✅ No need to manage multiple API clients

#### Cons
- ❌ Doesn't connect to MCP servers (you still need MCP SDK)
- ❌ OpenRouter forces OpenAI format (less flexible)
- ❌ Portkey MCP Gateway not ready yet
- ❌ Additional cost (per-token markup or subscription)
- ❌ Dependency on third-party service
- ❌ Data goes through external proxy (privacy concern)

#### Verdict for Your Use Case
**🔴 Not Recommended** - Adds external dependency and cost without solving MCP integration. Better options:
- If you want proxy benefits → Use LiteLLM Proxy (self-hosted)
- If you need MCP integration → Use MCP SDK directly

---

### Option 5: MCP Python SDK + Custom Multi-Provider Wrapper ⭐ RECOMMENDED

**Description:** Use MCP SDK for tools + lightweight custom wrapper for LLM providers

#### MCP Tool Support
✅ **Native and Complete** - Official MCP SDK

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to MCP servers
async with stdio_client(
    StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem", "/path"]
    )
) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize connection
        await session.initialize()

        # List available tools
        tools = await session.list_tools()

        # Execute tool
        result = await session.call_tool("get_stock_info", {"ticker": "AAPL"})
```

#### Multi-Provider Support
✅ **Custom Implementation** - Simple abstraction layer

**Architecture:**
```python
from typing import Protocol, List, Dict, Any
from mcp import ClientSession

class LLMProvider(Protocol):
    """Interface for LLM providers"""

    async def chat(
        self,
        messages: List[Dict],
        tools: List[Dict]  # MCP tools in provider format
    ) -> Dict:
        """Send chat request with tools"""
        ...

    def convert_tools(self, mcp_tools: List) -> List[Dict]:
        """Convert MCP tools to provider format"""
        ...

    def extract_tool_calls(self, response: Dict) -> List[Dict]:
        """Extract tool calls from response"""
        ...

class ClaudeProvider:
    def __init__(self, api_key: str):
        from anthropic import Anthropic
        self.client = Anthropic(api_key=api_key)

    async def chat(self, messages, tools):
        response = self.client.messages.create(
            model="claude-sonnet-4-5",
            messages=messages,
            tools=tools
        )
        return response

    def convert_tools(self, mcp_tools):
        """Convert MCP tools to Claude's input_schema format"""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.inputSchema
            }
            for tool in mcp_tools
        ]

    def extract_tool_calls(self, response):
        """Extract tool_use blocks from Claude response"""
        return [
            {
                "id": block.id,
                "name": block.name,
                "input": block.input
            }
            for block in response.content
            if block.type == "tool_use"
        ]

class OpenAIProvider:
    def __init__(self, api_key: str):
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)

    async def chat(self, messages, tools):
        response = await self.client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools
        )
        return response

    def convert_tools(self, mcp_tools):
        """Convert MCP tools to OpenAI's parameters format"""
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema
                }
            }
            for tool in mcp_tools
        ]

    def extract_tool_calls(self, response):
        """Extract tool_calls from OpenAI response"""
        if not response.choices[0].message.tool_calls:
            return []
        return [
            {
                "id": tc.id,
                "name": tc.function.name,
                "input": json.loads(tc.function.arguments)
            }
            for tc in response.choices[0].message.tool_calls
        ]

class GeminiProvider:
    def __init__(self, api_key: str):
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.client = genai.Client()

    async def chat(self, messages, tools):
        response = await self.client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=messages,
            tools=tools
        )
        return response

    def convert_tools(self, mcp_tools):
        """Convert MCP tools to Gemini's FunctionDeclaration format"""
        from google.generativeai.types import FunctionDeclaration, Tool

        return [
            Tool(function_declarations=[
                FunctionDeclaration(
                    name=tool.name,
                    description=tool.description,
                    parameters=tool.inputSchema
                )
                for tool in mcp_tools
            ])
        ]

    def extract_tool_calls(self, response):
        """Extract function_call parts from Gemini response"""
        tool_calls = []
        for part in response.candidates[0].content.parts:
            if hasattr(part, 'function_call'):
                tool_calls.append({
                    "id": None,  # Gemini doesn't provide IDs
                    "name": part.function_call.name,
                    "input": dict(part.function_call.args)
                })
        return tool_calls

# Unified agent class
class MultiProviderMCPAgent:
    def __init__(self, provider: LLMProvider, mcp_sessions: List[ClientSession]):
        self.provider = provider
        self.mcp_sessions = mcp_sessions
        self.tools = []

    async def initialize(self):
        """Get all tools from MCP servers"""
        for session in self.mcp_sessions:
            tools = await session.list_tools()
            self.tools.extend(tools)

    async def run(self, user_message: str):
        """ReAct loop"""
        messages = [{"role": "user", "content": user_message}]

        # Convert MCP tools to provider format
        provider_tools = self.provider.convert_tools(self.tools)

        for _ in range(10):  # Max 10 iterations
            # Get LLM response
            response = await self.provider.chat(messages, provider_tools)

            # Extract tool calls
            tool_calls = self.provider.extract_tool_calls(response)

            if not tool_calls:
                # No more tool calls, done
                return response

            # Execute tools via MCP
            for call in tool_calls:
                # Find the right MCP session for this tool
                for session in self.mcp_sessions:
                    try:
                        result = await session.call_tool(call["name"], call["input"])
                        # Add result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": call.get("id"),
                            "content": result.content
                        })
                        break
                    except:
                        continue

        return response
```

**Usage:**
```python
# Initialize
claude = ClaudeProvider(api_key=ANTHROPIC_API_KEY)
# OR
openai = OpenAIProvider(api_key=OPENAI_API_KEY)
# OR
gemini = GeminiProvider(api_key=GOOGLE_API_KEY)

# Connect to MCP servers
yfinance_session = await connect_to_mcp(...)
fred_session = await connect_to_mcp(...)
composer_session = await connect_to_mcp(...)

# Create agent
agent = MultiProviderMCPAgent(
    provider=claude,  # Swap provider here
    mcp_sessions=[yfinance_session, fred_session, composer_session]
)

await agent.initialize()
result = await agent.run("Create a trading strategy...")
```

#### Tool Calling Normalization
✅ **You Control It** - Clean abstraction per provider

**Effort:** ~100-150 lines total for 3 providers
- ClaudeProvider: ~40 lines
- OpenAIProvider: ~40 lines
- GeminiProvider: ~50 lines
- Shared interface: ~20 lines

#### Setup Complexity
🟢 **Low** - Minimal dependencies
```bash
pip install mcp anthropic openai google-generativeai
```

No frameworks, no proxies, no configuration files.

#### Code Simplicity
✅ **Simple and Transparent** - ~200 lines total
- MCP SDK handles tool connections
- Provider classes handle LLM-specific formats
- Agent class orchestrates the loop
- No magic, easy to debug

#### Production Ready
✅ **Yes** - You control everything
- MCP SDK is stable (official from Anthropic)
- Provider SDKs are official and mature
- Add your own error handling, retry logic
- Easy to add observability (just log the flow)

#### Community Support
✅ **Good** - Leverage existing resources
- MCP SDK docs: https://modelcontextprotocol.io/
- Provider SDKs have excellent docs
- Many examples in the wild (see GitHub projects)

#### Pros
- ✅ **Full control** - No framework lock-in
- ✅ **Minimal dependencies** - Only official SDKs
- ✅ **Easy to debug** - Transparent flow
- ✅ **Native MCP support** - Official SDK
- ✅ **Clean abstractions** - Protocol-based providers
- ✅ **Swappable providers** - One-line change
- ✅ **Production-ready** - Stable foundation
- ✅ **Fast to implement** - ~200 lines
- ✅ **Easy to extend** - Add new providers easily
- ✅ **No external services** - Self-contained

#### Cons
- ⚠️ **You implement retry logic** (~20 lines with tenacity)
- ⚠️ **You implement observability** (~10 lines with logging)
- ⚠️ **Manual format conversions** (but clean and explicit)
- ⚠️ **No built-in cost tracking** (add if needed)

#### Verdict for Your Use Case
**✅ STRONGLY RECOMMENDED** - Perfect balance for first-time agent builder:
- Learn the fundamentals (no magic)
- Production-ready foundation
- Minimal dependencies
- Full control for iteration
- Easy to understand and debug

---

### Option 6: Other Approaches

#### Hybrid: LiteLLM + MCP SDK
**Combine the best of both:**
```python
from litellm import completion
from mcp import ClientSession

# MCP SDK for tools
mcp_tools = await mcp_session.list_tools()

# Convert to OpenAI format (MCP → OpenAI)
openai_tools = convert_mcp_to_openai(mcp_tools)

# LiteLLM for multi-provider (handles OpenAI → Provider format)
response = completion(
    model="anthropic/claude-sonnet-4-5",  # or any provider
    messages=messages,
    tools=openai_tools  # LiteLLM converts to Claude format
)
```

**Pros:**
- ✅ Best of both: MCP SDK for tools, LiteLLM for providers
- ✅ Less code than full custom (no provider classes)
- ✅ LiteLLM handles retry, fallback, cost tracking

**Cons:**
- ⚠️ Still need MCP → OpenAI conversion (~30 lines)
- ⚠️ Extra dependency (LiteLLM)
- ⚠️ Two abstractions to understand

**Verdict:** 🟡 **Viable Alternative** - Good if you want LiteLLM's features (retry, fallback, observability)

---

#### Strands Agents SDK
**Production-ready framework with native MCP support**

From PyPI: https://pypi.org/project/strands-agents/

```python
from strands_agents import Agent

agent = Agent(
    model="anthropic/claude-sonnet-4-5",
    tools=[...]  # MCP tools supported
)
```

**Pros:**
- ✅ Native MCP support
- ✅ Model-agnostic (Bedrock, Anthropic, Gemini, OpenAI)
- ✅ Production-ready framework

**Cons:**
- ⚠️ New framework (less community)
- ⚠️ Another abstraction to learn
- ⚠️ Limited documentation

**Verdict:** 🟡 **Worth Watching** - Promising but unproven for your use case

---

## Comparison Summary Table

| Criterion | LiteLLM | Direct Custom | LangChain | OpenRouter/Portkey | **MCP SDK + Custom** | Hybrid |
|-----------|---------|---------------|-----------|--------------------|--------------------|--------|
| **MCP Tool Support** | ⚠️ Partial (need MCP SDK) | ✅ Manual | ✅ Official adapters | ❌ Separate | ✅ Native SDK | ✅ Native SDK |
| **Multi-Provider** | ✅ Excellent | ✅ Full control | ✅ Built-in | ✅ Excellent | ✅ Custom (simple) | ✅ LiteLLM |
| **Setup Complexity** | 🟡 Medium | 🟢 Low | 🔴 High | 🟢 Low | 🟢 Low | 🟡 Medium |
| **Code to Write** | ~50 lines + MCP | 300-500 lines | ~50 lines | ~100 lines | **~200 lines** | ~100 lines |
| **Tool Normalization** | ✅ Automatic | ⚠️ Manual | ✅ Automatic | ✅ Automatic | ✅ You control | ✅ Automatic |
| **Production Ready** | ✅ Mature | 🟡 Yours | ✅ Mature | ✅ Mature | ✅ Stable | ✅ Stable |
| **Community** | ✅ Excellent | ❌ None | ✅ Excellent | ✅ Good | ✅ Good | ✅ Good |
| **Dependencies** | Medium | Minimal | **Heavy** | Minimal | **Minimal** | Medium |
| **Debugging** | 🟡 Two layers | ✅ Transparent | 🔴 Complex | 🟡 Proxy layer | ✅ Transparent | 🟡 Two layers |
| **Control** | 🟡 Framework | ✅ Full | 🔴 Framework | 🔴 Proxy | ✅ Full | 🟡 Shared |
| **Learning Curve** | 🟢 Low | 🟡 Medium | 🔴 High | 🟢 Low | 🟢 Low | 🟡 Medium |
| **Cost** | Free | Free | Free | $$$ | Free | Free |
| **Recommended** | 🟡 | 🔴 | 🟡 | 🔴 | ✅ ⭐ | 🟡 |

---

## Final Recommendation

### ⭐ **Option 5: MCP Python SDK + Custom Multi-Provider Wrapper**

**Why this is best for your use case:**

1. **First-time Agent Builder Friendly**
   - Clean, understandable architecture
   - No framework magic
   - Learn the fundamentals

2. **Production-Ready**
   - Official MCP SDK (stable)
   - Official provider SDKs (mature)
   - Easy to add error handling, retry, observability

3. **Minimal Dependencies**
   - Only `mcp`, `anthropic`, `openai`, `google-generativeai`
   - No frameworks, no proxies
   - Fast installation, no config files

4. **Full Control**
   - Understand exactly what's happening
   - Easy to debug
   - Easy to extend (add new providers, tools, features)

5. **Simple Code (~200 lines)**
   - 3 provider classes (~40-50 lines each)
   - 1 agent class (~80 lines)
   - Clean protocol-based design

6. **Perfect Fit for Trading Strategy Agent**
   - MCP SDK connects to yfinance, FRED, Composer MCPs
   - Provider abstraction for Claude, GPT-4, Gemini
   - Easy to iterate and experiment

---

## Architecture Diagram (Recommended Approach)

```
┌─────────────────────────────────────────────────────────────────┐
│                    Trading Strategy Agent                       │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │              MultiProviderMCPAgent                        │ │
│  │                                                           │ │
│  │  • ReAct loop orchestration                              │ │
│  │  • Message history management                            │ │
│  │  • Tool execution routing                                │ │
│  └──────────────┬────────────────────────────┬──────────────┘ │
│                 │                            │                 │
│                 ▼                            ▼                 │
│  ┌──────────────────────────┐  ┌───────────────────────────┐  │
│  │   LLMProvider Interface  │  │  MCP Client Sessions      │  │
│  ├──────────────────────────┤  ├───────────────────────────┤  │
│  │                          │  │                           │  │
│  │  ClaudeProvider          │  │  yfinance MCP Session     │  │
│  │  ├─ convert_tools()      │  │  ├─ list_tools()         │  │
│  │  ├─ chat()               │  │  └─ call_tool()          │  │
│  │  └─ extract_tool_calls() │  │                           │  │
│  │                          │  │  FRED MCP Session         │  │
│  │  OpenAIProvider          │  │  ├─ list_tools()         │  │
│  │  ├─ convert_tools()      │  │  └─ call_tool()          │  │
│  │  ├─ chat()               │  │                           │  │
│  │  └─ extract_tool_calls() │  │  Composer MCP Session     │  │
│  │                          │  │  ├─ list_tools()         │  │
│  │  GeminiProvider          │  │  └─ call_tool()          │  │
│  │  ├─ convert_tools()      │  │                           │  │
│  │  ├─ chat()               │  └───────────────────────────┘  │
│  │  └─ extract_tool_calls() │                                 │
│  └──────────────────────────┘                                 │
└─────────────┬──────────────────────────────┬──────────────────┘
              │                              │
              ▼                              ▼
   ┌────────────────────┐         ┌──────────────────────┐
   │   LLM Provider     │         │   MCP Servers        │
   │   APIs             │         │                      │
   ├────────────────────┤         ├──────────────────────┤
   │ • Claude API       │         │ • yfinance MCP       │
   │ • OpenAI API       │         │ • FRED MCP           │
   │ • Gemini API       │         │ • Composer MCP       │
   └────────────────────┘         └──────────────────────┘
```

**Key Components:**

1. **MultiProviderMCPAgent**
   - Orchestrates the ReAct loop
   - Manages conversation state
   - Routes tool calls to MCP sessions

2. **LLMProvider Interface**
   - Protocol defining provider contract
   - 3 methods: `convert_tools()`, `chat()`, `extract_tool_calls()`
   - Swappable implementations

3. **MCP Client Sessions**
   - Official MCP SDK connections
   - One session per MCP server
   - Handle tool listing and execution

**Data Flow:**

```
1. User Request
   ↓
2. Agent → MCP Sessions → list_tools()
   ↓
3. Agent → Provider.convert_tools(mcp_tools)
   ↓
4. Agent → Provider.chat(messages, provider_tools)
   ↓
5. Provider → LLM API (Claude/OpenAI/Gemini)
   ↓
6. LLM Response → Provider.extract_tool_calls(response)
   ↓
7. Tool Calls → MCP Sessions → call_tool(name, args)
   ↓
8. Tool Results → Agent → Provider.chat(...) [loop]
   ↓
9. Final Response → User
```

---

## Implementation Example (Recommended)

### File Structure

```
src/agent/
├── __init__.py
├── agent.py                    # MultiProviderMCPAgent class
├── providers/
│   ├── __init__.py
│   ├── protocol.py             # LLMProvider Protocol
│   ├── claude.py               # ClaudeProvider
│   ├── openai.py               # OpenAIProvider
│   └── gemini.py               # GeminiProvider
├── mcp_manager.py              # MCP session management
└── prompts/
    └── system_prompt.md        # Agent instructions
```

### Core Code Sample

**providers/protocol.py** (~20 lines)
```python
from typing import Protocol, List, Dict, Any

class LLMProvider(Protocol):
    """Interface for LLM providers"""

    async def chat(
        self,
        messages: List[Dict],
        tools: List[Dict]
    ) -> Any:
        """Send chat request with tools"""
        ...

    def convert_tools(self, mcp_tools: List) -> List[Dict]:
        """Convert MCP tools to provider format"""
        ...

    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """Extract tool calls from response

        Returns:
            List of {"id": str, "name": str, "input": dict}
        """
        ...
```

**providers/claude.py** (~40 lines)
```python
from typing import List, Dict, Any
from anthropic import Anthropic

class ClaudeProvider:
    def __init__(self, api_key: str, model: str = "claude-sonnet-4-5"):
        self.client = Anthropic(api_key=api_key)
        self.model = model

    async def chat(self, messages: List[Dict], tools: List[Dict]) -> Any:
        return self.client.messages.create(
            model=self.model,
            messages=messages,
            tools=tools,
            max_tokens=4096
        )

    def convert_tools(self, mcp_tools: List) -> List[Dict]:
        """Convert MCP tools to Claude's input_schema format"""
        return [
            {
                "name": tool.name,
                "description": tool.description or "",
                "input_schema": tool.inputSchema
            }
            for tool in mcp_tools
        ]

    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """Extract tool_use blocks from Claude response"""
        tool_calls = []
        for block in response.content:
            if block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })
        return tool_calls
```

**mcp_manager.py** (~50 lines)
```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from typing import List, Dict

class MCPManager:
    def __init__(self):
        self.sessions: List[ClientSession] = []
        self.tools: List = []

    async def add_server(self, command: str, args: List[str]):
        """Connect to an MCP server via stdio"""
        params = StdioServerParameters(command=command, args=args)

        read, write = await stdio_client(params).__aenter__()
        session = ClientSession(read, write)
        await session.initialize()

        self.sessions.append(session)

    async def add_http_server(self, url: str, headers: Dict = None):
        """Connect to an MCP server via HTTP"""
        # Implementation for HTTP transport
        pass

    async def refresh_tools(self):
        """Get all tools from all connected servers"""
        self.tools = []
        for session in self.sessions:
            session_tools = await session.list_tools()
            self.tools.extend(session_tools.tools)
        return self.tools

    async def call_tool(self, name: str, arguments: Dict) -> Any:
        """Execute a tool by name"""
        for session in self.sessions:
            try:
                result = await session.call_tool(name, arguments)
                return result
            except Exception:
                continue
        raise ValueError(f"Tool {name} not found in any session")
```

**agent.py** (~80 lines)
```python
from typing import List, Dict, Any
from .providers.protocol import LLMProvider
from .mcp_manager import MCPManager

class MultiProviderMCPAgent:
    def __init__(
        self,
        provider: LLMProvider,
        mcp_manager: MCPManager,
        system_prompt: str = ""
    ):
        self.provider = provider
        self.mcp = mcp_manager
        self.system_prompt = system_prompt
        self.messages: List[Dict] = []

    async def run(
        self,
        user_message: str,
        max_iterations: int = 15
    ) -> str:
        """Execute ReAct loop"""

        # Initialize tools
        mcp_tools = await self.mcp.refresh_tools()
        provider_tools = self.provider.convert_tools(mcp_tools)

        # Add user message
        self.messages.append({
            "role": "user",
            "content": user_message
        })

        # ReAct loop
        for iteration in range(max_iterations):
            print(f"[Iteration {iteration + 1}]")

            # Get LLM response
            response = await self.provider.chat(
                messages=self.messages,
                tools=provider_tools
            )

            # Extract tool calls
            tool_calls = self.provider.extract_tool_calls(response)

            if not tool_calls:
                # No tool calls, we're done
                final_text = self._extract_text(response)
                print(f"[Final Response] {final_text}")
                return final_text

            # Execute tools
            for call in tool_calls:
                print(f"[Tool Call] {call['name']}({call['input']})")

                try:
                    result = await self.mcp.call_tool(
                        call["name"],
                        call["input"]
                    )
                    print(f"[Tool Result] {result.content}")

                    # Add tool result to messages
                    self._add_tool_result(call, result)

                except Exception as e:
                    print(f"[Tool Error] {e}")
                    self._add_tool_error(call, str(e))

        return "Max iterations reached"

    def _extract_text(self, response: Any) -> str:
        """Extract text content from provider response"""
        # Provider-specific implementation
        if hasattr(response, 'content'):
            # Claude
            for block in response.content:
                if block.type == "text":
                    return block.text
        elif hasattr(response, 'choices'):
            # OpenAI
            return response.choices[0].message.content
        # Add Gemini handling
        return str(response)

    def _add_tool_result(self, call: Dict, result: Any):
        """Add tool result to message history"""
        # Provider-specific formatting
        self.messages.append({
            "role": "tool",
            "tool_call_id": call.get("id"),
            "name": call["name"],
            "content": str(result.content)
        })

    def _add_tool_error(self, call: Dict, error: str):
        """Add tool error to message history"""
        self.messages.append({
            "role": "tool",
            "tool_call_id": call.get("id"),
            "name": call["name"],
            "content": f"Error: {error}",
            "is_error": True
        })
```

**Usage:**

```python
import asyncio
from agent import MultiProviderMCPAgent
from agent.providers.claude import ClaudeProvider
from agent.mcp_manager import MCPManager

async def main():
    # 1. Setup MCP connections
    mcp = MCPManager()

    # Add yfinance MCP (HTTP)
    await mcp.add_http_server("http://localhost:8000/mcp")

    # Add FRED MCP (stdio)
    await mcp.add_server(
        command="npx",
        args=["-y", "@stefanoamorelli/fred-mcp-server"]
    )

    # Add Composer MCP (HTTP with auth)
    await mcp.add_http_server(
        url="https://ai.composer.trade/mcp",
        headers={"Authorization": f"Basic {base64_creds}"}
    )

    # 2. Choose provider
    provider = ClaudeProvider(api_key=ANTHROPIC_API_KEY)
    # OR: provider = OpenAIProvider(api_key=OPENAI_API_KEY)
    # OR: provider = GeminiProvider(api_key=GOOGLE_API_KEY)

    # 3. Create agent
    agent = MultiProviderMCPAgent(
        provider=provider,
        mcp_manager=mcp,
        system_prompt="You are a trading strategy expert..."
    )

    # 4. Run
    result = await agent.run(
        "Create a momentum-based trading strategy for the current market regime"
    )

    print(f"\n\nFinal Result:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Critical Implementation Notes

### 1. MCP Tool Format vs Provider Tool Format

**MCP Tool Schema:**
```json
{
  "name": "get_stock_info",
  "description": "Get stock information",
  "inputSchema": {
    "type": "object",
    "properties": {
      "ticker": {"type": "string"}
    },
    "required": ["ticker"]
  }
}
```

**Claude Format:**
```json
{
  "name": "get_stock_info",
  "description": "Get stock information",
  "input_schema": {
    "type": "object",
    "properties": {
      "ticker": {"type": "string"}
    },
    "required": ["ticker"]
  }
}
```

**OpenAI Format:**
```json
{
  "type": "function",
  "function": {
    "name": "get_stock_info",
    "description": "Get stock information",
    "parameters": {
      "type": "object",
      "properties": {
        "ticker": {"type": "string"}
      },
      "required": ["ticker"]
    }
  }
}
```

**Gemini Format:**
```python
from google.generativeai.types import FunctionDeclaration, Tool

Tool(
    function_declarations=[
        FunctionDeclaration(
            name="get_stock_info",
            description="Get stock information",
            parameters={
                "type": "object",
                "properties": {
                    "ticker": {"type": "string"}
                },
                "required": ["ticker"]
            }
        )
    ]
)
```

### 2. Tool Call Response Handling

**Claude Response:**
```json
{
  "content": [
    {
      "type": "text",
      "text": "I'll get the stock info..."
    },
    {
      "type": "tool_use",
      "id": "toolu_123",
      "name": "get_stock_info",
      "input": {"ticker": "AAPL"}
    }
  ]
}
```

**OpenAI Response:**
```json
{
  "choices": [{
    "message": {
      "content": null,
      "tool_calls": [{
        "id": "call_123",
        "type": "function",
        "function": {
          "name": "get_stock_info",
          "arguments": "{\"ticker\": \"AAPL\"}"
        }
      }]
    }
  }]
}
```

**Gemini Response:**
```python
response.candidates[0].content.parts[0].function_call
# FunctionCall(name="get_stock_info", args={"ticker": "AAPL"})
```

### 3. Tool Result Injection

**Claude:**
```python
messages.append({
    "role": "user",
    "content": [
        {
            "type": "tool_result",
            "tool_use_id": "toolu_123",
            "content": str(result)
        }
    ]
})
```

**OpenAI:**
```python
messages.append({
    "role": "tool",
    "tool_call_id": "call_123",
    "content": str(result)
})
```

**Gemini:**
```python
from google.generativeai.types import Part

messages.append(
    Part.from_function_response(
        name="get_stock_info",
        response={"result": str(result)}
    )
)
```

---

## Next Steps

### Week 1: Core Implementation
1. ✅ Choose approach: **MCP SDK + Custom Multi-Provider**
2. Setup project structure
3. Implement `LLMProvider` protocol
4. Implement `ClaudeProvider` (start here)
5. Implement `MCPManager`
6. Implement `MultiProviderMCPAgent`
7. Test with yfinance MCP

### Week 2: Multi-Provider Support
8. Implement `OpenAIProvider`
9. Implement `GeminiProvider`
10. Test provider switching
11. Add error handling and retry logic
12. Connect FRED MCP
13. Connect Composer MCP

### Week 3: Strategy Creation Workflow
14. Load strategy creation prompt
15. Implement charter generation
16. Test end-to-end strategy creation
17. Add observability (logging)
18. Performance testing

### Week 4: Polish & Testing
19. Write unit tests
20. Write integration tests
21. Documentation
22. Compare outputs across providers
23. Production readiness checklist

---

## Recommended Resources

### Official Documentation
- **MCP SDK:** https://modelcontextprotocol.io/
- **Claude API:** https://docs.anthropic.com/
- **OpenAI API:** https://platform.openai.com/docs/
- **Gemini API:** https://ai.google.dev/gemini-api/docs/

### Example Implementations
- **poly-mcp-client:** https://github.com/yo-ban/poly-mcp-client
- **simple-mcp-client:** https://github.com/allenbijo/simple-mcp-client
- **Phil Schmid MCP Example:** https://www.philschmid.de/mcp-example-llama

### Learning Resources
- **Medium Article (Multi-Provider):** "Beyond Claude: Using OpenAI and Google Gemini Models with MCP Servers"
- **LiteLLM Docs:** https://docs.litellm.ai/
- **LangChain MCP Adapters:** https://langchain-ai.github.io/langgraph/agents/mcp/

---

## Conclusion

For a first-time agent builder working on a trading strategy creation agent, **MCP Python SDK + Custom Multi-Provider Wrapper** is the ideal choice:

- ✅ **Learn fundamentals** - No framework magic obscuring what's happening
- ✅ **Production-ready** - Stable foundation with official SDKs
- ✅ **Minimal complexity** - ~200 lines of clean, understandable code
- ✅ **Full control** - Easy to debug, extend, and customize
- ✅ **Perfect fit** - Designed exactly for your use case (MCP tools + multi-provider LLMs)

Alternative viable options:
- **Hybrid (LiteLLM + MCP SDK)** - If you want built-in retry/fallback/observability
- **LangChain** - If you plan to use the broader LangChain ecosystem

Avoid:
- **Direct Custom Implementation** - Too much boilerplate
- **OpenRouter/Portkey** - Doesn't solve MCP integration, adds cost
- **Pure LiteLLM** - Doesn't connect to MCP servers directly

Good luck with your implementation! 🚀
