# python sdk to mcp converter

converts any python sdk into an mcp server. discovers methods automatically, generates json schemas, exposes via mcp protocol.

tested on: kubernetes, github, azure, aws (boto3), stripe, requests, and standard python libraries.

## quick start

```bash
pip install -r requirements.txt
cd demo_agent
cp .env.example .env
nano .env  # add OPENAI_API_KEY
python app.py
```

see `SETUP.md` for detailed instructions and credential configuration.

## how it works

**discovery**: uses python `inspect` to find methods from any module. handles simple modules (`os`, `json`), client sdks (github, kubernetes), and azure operation groups.

**schemas**: converts function signatures to json schemas. extracts types from annotations and descriptions from docstrings.

**protocol**: implements json-rpc 2.0 over stdio. supports `tools/list` (discovery) and `tools/call` (execution).

**execution**: validates inputs, injects auth, executes with retries and timeout, caches results, redacts secrets.

**llm usage**: optional openai api calls during startup to enhance schema descriptions. disabled by default. core functionality works without it.

## run the server directly

```bash
export SDKS="os,requests,kubernetes"
python server.py
```

reads json-rpc from stdin, writes responses to stdout.

## configuration

environment variables for server behavior:

```bash
SDKS="os,boto3"              # which sdks to load
ALLOW_DANGEROUS=false        # filter delete/remove operations
ENABLE_CACHE=true            # cache results
MAX_RETRIES=3                # retry failed calls
```

sdk credentials in `demo_agent/.env`:

```bash
OPENAI_API_KEY=sk-...        # required for demo ui
GITHUB_TOKEN=ghp_...         # optional
AZURE_TENANT_ID=...          # optional
AWS_ACCESS_KEY_ID=...        # optional
```

## testing

```bash
cd core_sdk_to_mcp_tool
python test_core_functionality.py
```

## files

- `server.py` - mcp server main loop
- `reflection.py` - method discovery
- `schema_gen.py` - json schema generation
- `executor.py` - execution with retry/cache
- `mcp_protocol.py` - json-rpc handlers
- `auth.py` - credential injection
- `demo_agent/app.py` - terminal ui demo

## supported sdks

works with any python module. special handling for:
- client sdks: instantiates with credentials (github, kubernetes)
- azure: discovers operation groups (resource_groups, virtual_machines)
- factory patterns: boto3, stripe

## limitations

- openai limits to 128 tools per agent
- requires type hints for accurate schemas
- authentication must be pre-configured
