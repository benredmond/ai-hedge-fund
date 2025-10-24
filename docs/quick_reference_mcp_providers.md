# Quick Reference: Multi-Provider MCP Integration

## TL;DR - What Should I Use?

### ⭐ Recommended: MCP SDK + Custom Wrapper
```bash
pip install mcp anthropic openai google-generativeai
```

**Why:** Clean, simple, full control. ~200 lines total.

**Use if:**
- First-time agent builder
- Want to learn fundamentals
- Need production-ready foundation
- Want minimal dependencies

---

## Quick Decision Tree

```
Do you already use LangChain in your stack?
├─ YES → Use LangChain MCP Adapters
│         (Official integration, fits your workflow)
│
└─ NO → Do you need built-in retry/fallback/observability?
         ├─ YES → Use LiteLLM + MCP SDK Hybrid
         │         (Best of both worlds)
         │
         └─ NO → Use MCP SDK + Custom Wrapper ⭐
                   (Recommended for most cases)
```

---

## One-Page Comparison

| Approach | MCP Support | Code Complexity | Dependencies | Best For |
|----------|-------------|-----------------|--------------|----------|
| **MCP SDK + Custom** ⭐ | ✅ Native | 🟢 ~200 lines | Minimal | **First-timers, production apps** |
| LiteLLM + MCP SDK | ⚠️ Hybrid | 🟢 ~100 lines | Medium | Built-in retry/fallback needed |
| LangChain MCP | ✅ Official | 🟡 ~50 lines | Heavy | Already using LangChain |
| Direct Custom | ✅ Manual | 🔴 ~500 lines | Minimal | Learning exercise only |
| OpenRouter/Portkey | ❌ Separate | 🟡 ~100 lines | Medium + $$ | Not recommended |

---

## Key Technical Differences

### Tool Format Conversion Required

**MCP Tool:**
```json
{
  "name": "get_stock_info",
  "inputSchema": { /* JSON Schema */ }
}
```

**Claude:**
```json
{
  "name": "get_stock_info",
  "input_schema": { /* JSON Schema */ }
}
```

**OpenAI:**
```json
{
  "type": "function",
  "function": {
    "name": "get_stock_info",
    "parameters": { /* JSON Schema */ }
  }
}
```

**Gemini:**
```python
Tool(function_declarations=[
  FunctionDeclaration(
    name="get_stock_info",
    parameters={ /* JSON Schema */ }
  )
])
```

### Tool Response Extraction

| Provider | Response Location | ID Field |
|----------|-------------------|----------|
| Claude | `response.content[].tool_use` | `block.id` |
| OpenAI | `response.choices[0].message.tool_calls[]` | `tool_call.id` |
| Gemini | `response.candidates[0].content.parts[].function_call` | None |

---

## Minimal Working Example (Recommended Approach)

### providers/claude.py
```python
from anthropic import Anthropic

class ClaudeProvider:
    def __init__(self, api_key: str):
        self.client = Anthropic(api_key=api_key)

    def convert_tools(self, mcp_tools):
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.inputSchema
            }
            for t in mcp_tools
        ]

    def chat(self, messages, tools):
        return self.client.messages.create(
            model="claude-sonnet-4-5",
            messages=messages,
            tools=tools
        )

    def extract_tool_calls(self, response):
        return [
            {"id": b.id, "name": b.name, "input": b.input}
            for b in response.content
            if b.type == "tool_use"
        ]
```

### agent.py
```python
from mcp import ClientSession

class Agent:
    def __init__(self, provider, mcp_sessions):
        self.provider = provider
        self.mcp_sessions = mcp_sessions

    async def run(self, user_message):
        # Get MCP tools
        mcp_tools = []
        for session in self.mcp_sessions:
            tools = await session.list_tools()
            mcp_tools.extend(tools.tools)

        # Convert to provider format
        provider_tools = self.provider.convert_tools(mcp_tools)

        messages = [{"role": "user", "content": user_message}]

        # ReAct loop
        for _ in range(10):
            response = self.provider.chat(messages, provider_tools)
            tool_calls = self.provider.extract_tool_calls(response)

            if not tool_calls:
                return response  # Done

            # Execute tools
            for call in tool_calls:
                for session in self.mcp_sessions:
                    try:
                        result = await session.call_tool(
                            call["name"],
                            call["input"]
                        )
                        # Add result to messages
                        break
                    except:
                        continue

        return response
```

### Usage
```python
from agent import Agent
from providers.claude import ClaudeProvider
from mcp.client.stdio import stdio_client

# Connect to MCP
async with stdio_client(...) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()

        # Create agent
        provider = ClaudeProvider(api_key=API_KEY)
        agent = Agent(provider, [session])

        # Run
        result = await agent.run("Create a trading strategy")
```

**To swap providers:** Change one line:
```python
provider = ClaudeProvider(api_key=API_KEY)
# OR
provider = OpenAIProvider(api_key=API_KEY)
# OR
provider = GeminiProvider(api_key=API_KEY)
```

---

## Common Mistakes to Avoid

### ❌ Don't: Use LiteLLM Alone
```python
# This WON'T work - LiteLLM doesn't connect to MCP servers
from litellm import completion

response = completion(
    model="claude-sonnet-4-5",
    tools=???  # Where do MCP tools come from?
)
```

### ✅ Do: Use MCP SDK for Tools
```python
# Correct - MCP SDK connects to servers
from mcp import ClientSession

session = ClientSession(...)
mcp_tools = await session.list_tools()
```

### ❌ Don't: Confuse MCP with LLM Provider
- **MCP** = Tool protocol (yfinance, FRED, Composer)
- **LLM Provider** = Reasoning engine (Claude, GPT-4, Gemini)
- You need **both**

### ✅ Do: Understand the Separation
```
MCP Servers → MCP SDK → Your Agent → LLM Provider → LLM API
(Tools)                                (Reasoning)
```

---

## FAQ

**Q: Can LiteLLM replace MCP SDK?**
A: No. LiteLLM is for LLM provider abstraction. MCP SDK is for connecting to MCP tool servers. Different purposes.

**Q: Do I need both LiteLLM and MCP SDK?**
A: Only if you want LiteLLM's features (retry, fallback, cost tracking). Otherwise, MCP SDK + custom wrapper is simpler.

**Q: What about LangChain?**
A: Good if you already use LangChain. Otherwise, it's framework overhead you don't need.

**Q: Why not just write custom code for everything?**
A: MCP SDK is the official, stable way to connect to MCP servers. Don't reinvent it.

**Q: Can I use the same code for all three providers?**
A: Yes, with a provider abstraction. See minimal example above.

**Q: How do I handle tool format differences?**
A: Provider classes convert MCP format to provider-specific format. ~10 lines per provider.

**Q: Is this production-ready?**
A: Yes. MCP SDK is official from Anthropic. Provider SDKs are mature. Add your own error handling.

**Q: How do I add retry logic?**
A: Use `tenacity` library:
```python
from tenacity import retry, stop_after_attempt

@retry(stop=stop_after_attempt(3))
async def chat_with_retry(self, messages, tools):
    return await self.provider.chat(messages, tools)
```

**Q: How do I add observability?**
A: Log at key points:
```python
import logging

logger.info(f"Tool call: {call['name']}({call['input']})")
logger.info(f"Tool result: {result}")
```

---

## MCP Servers for Your Project

### yfinance MCP
Already integrated in Claude Code environment.

### FRED MCP
```bash
npx -y @smithery/cli install @stefanoamorelli/fred-mcp-server --client claude
```

**Usage:**
```python
await mcp.add_server(
    command="npx",
    args=["-y", "@stefanoamorelli/fred-mcp-server"]
)
```

### Composer MCP
HTTP endpoint: `https://ai.composer.trade/mcp`

**Usage:**
```python
import base64

creds = base64.b64encode(
    f"{COMPOSER_API_KEY}:{COMPOSER_API_SECRET}".encode()
).decode()

await mcp.add_http_server(
    url="https://ai.composer.trade/mcp",
    headers={"Authorization": f"Basic {creds}"}
)
```

---

## Implementation Checklist

### Week 1: Foundation
- [ ] Install dependencies: `pip install mcp anthropic openai google-generativeai`
- [ ] Create `providers/protocol.py` (Protocol interface)
- [ ] Create `providers/claude.py` (ClaudeProvider)
- [ ] Create `mcp_manager.py` (MCP session management)
- [ ] Create `agent.py` (MultiProviderMCPAgent)
- [ ] Test with yfinance MCP

### Week 2: Multi-Provider
- [ ] Create `providers/openai.py` (OpenAIProvider)
- [ ] Create `providers/gemini.py` (GeminiProvider)
- [ ] Test provider switching
- [ ] Add FRED MCP connection
- [ ] Add Composer MCP connection
- [ ] Add error handling

### Week 3: Strategy Creation
- [ ] Load strategy creation prompt
- [ ] Implement ReAct loop
- [ ] Test end-to-end
- [ ] Add retry logic
- [ ] Add logging/observability

### Week 4: Polish
- [ ] Write unit tests
- [ ] Write integration tests
- [ ] Compare outputs across providers
- [ ] Documentation
- [ ] Production readiness review

---

## Resources

### Official Docs
- MCP SDK: https://modelcontextprotocol.io/
- Claude API: https://docs.anthropic.com/
- OpenAI API: https://platform.openai.com/docs/
- Gemini API: https://ai.google.dev/gemini-api/docs/

### Example Code
- poly-mcp-client: https://github.com/yo-ban/poly-mcp-client
- simple-mcp-client: https://github.com/allenbijo/simple-mcp-client

### Tutorials
- "Beyond Claude: Using OpenAI and Google Gemini Models with MCP Servers" (Medium)
- "How to use Anthropic MCP Server with open LLMs, OpenAI or Google Gemini" (philschmid.de)

---

## Final Recommendation

**Use MCP SDK + Custom Multi-Provider Wrapper**

**Reason:** Clean, simple, production-ready, minimal dependencies, full control.

**Total Code:** ~200 lines
**Setup Time:** ~1 hour
**Learning Curve:** Low (understand fundamentals, no magic)
**Production Ready:** Yes (add retry/logging as needed)

**Alternative:** If you need built-in retry/fallback/cost tracking → Use LiteLLM + MCP SDK Hybrid

**Avoid:** Direct custom implementation (too much code), OpenRouter/Portkey (doesn't solve MCP), pure LangChain (framework overhead)
