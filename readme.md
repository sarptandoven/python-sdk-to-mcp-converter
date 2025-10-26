# python sdk to mcp converter

automatically converts python sdks into mcp servers. discovers methods through reflection, generates schemas, handles authentication, and provides safety guardrails.

## features

- automatic method discovery from any python module
- json schema generation with optional llm enhancement
- authentication support for kubernetes, github, azure, aws
- safety filtering for dangerous operations
- pagination detection and handling
- secret redaction in responses
- retry logic with exponential backoff
- timeout handling
- comprehensive test coverage
- stdio transport

## installation

```bash
pip install kubernetes PyGithub azure-identity openai
```

## usage

basic usage:

```bash
python server.py
```

with specific sdks:

```bash
SDKS=kubernetes,github python server.py
```

with llm schema enhancement:

```bash
OPENAI_API_KEY=sk-xxx USE_LLM=true python server.py
```

allow dangerous operations (use carefully):

```bash
ALLOW_DANGEROUS=true python server.py
```

## configuration

all configuration via environment variables:

- `SDKS` - comma-separated list of sdk modules (default: os)
- `ALLOW_DANGEROUS` - allow create/update/delete operations (default: false)
- `USE_LLM` - enable llm schema enhancement (default: false)
- `OPENAI_API_KEY` - openai api key (required if USE_LLM=true)
- `OPENAI_MODEL` - openai model to use (default: gpt-3.5-turbo)
- `MAX_ITEMS` - max items for pagination (default: 100)
- `REDACT_SECRETS` - redact secrets in responses (default: true)
- `MAX_RETRIES` - max retry attempts (default: 3)
- `TIMEOUT` - timeout in seconds (default: 30)

## authentication

set these environment variables for sdk authentication:

```bash
export GITHUB_TOKEN=ghp_xxx
export KUBECONFIG=/path/to/kubeconfig
export AZURE_CLIENT_ID=xxx
export AZURE_TENANT_ID=xxx
export AZURE_CLIENT_SECRET=xxx
```

the server automatically detects and injects the right auth for each sdk.

## safety features

by default, dangerous operations are blocked:
- delete, remove, destroy
- create, update, patch
- write operations

secrets are automatically redacted from responses:
- passwords, tokens, api keys
- any field containing "password", "token", "key", "secret"

## testing

run all tests:

```bash
python test_reflection.py
python test_safety.py
python test_executor.py
python test_integration.py
```

## example usage

start the server:

```bash
SDKS=os python server.py
```

list available tools:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python server.py
```

call a tool:

```bash
echo '{"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"os.getcwd","arguments":{}}}' | python server.py
```

get server info:

```bash
echo '{"jsonrpc":"2.0","id":3,"method":"server/info","params":{}}' | python server.py
```

## architecture

```
server.py           - main server with request handling
mcp_protocol.py     - mcp json-rpc implementation
reflection.py       - method discovery engine
schema_gen.py       - schema generation with llm
auth.py             - authentication providers
safety.py           - safety checks and redaction
pagination.py       - pagination detection
executor.py         - execution with retry/timeout
config.py           - configuration management
```

## adding new sdks

just add the module name to the SDKS environment variable:

```bash
SDKS=stripe,twilio,notion python server.py
```

the server will automatically discover and expose all methods.

## known limitations

- multi-page collection not fully implemented yet
- async function support needs improvement
- some edge cases in type coercion
- llm schema enhancement could be smarter

## todo

- implement full multi-page collection
- better async function handling
- more sophisticated type coercion
- caching layer
- rate limiting
- openapi export

## development

project is at ~80% completion. core functionality is solid but some features need polish.

## notes

this is a near-production version. has been tested with kubernetes, github, azure, and various other sdks. most common use cases should work well.
