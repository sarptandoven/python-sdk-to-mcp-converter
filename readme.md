# python sdk to mcp converter

converts python sdks into mcp servers automatically. discovers methods via reflection and exposes them through the mcp protocol.

## features

- automatic method discovery from python modules
- json schema generation from type hints
- basic authentication support (kubernetes, github, azure)
- safety filtering for dangerous operations
- pagination detection
- secret redaction in responses
- stdio transport

## usage

```bash
# basic usage
python server.py

# load specific sdks
SDKS=kubernetes,github python server.py

# allow dangerous operations (use carefully)
ALLOW_DANGEROUS=true python server.py
```

## authentication

set environment variables for sdk authentication:

```bash
export GITHUB_TOKEN=your_token
export KUBECONFIG=/path/to/config
# etc
```

the server will try to inject auth automatically based on the sdk being used.

## safety

by default, dangerous operations like delete, update, create are blocked. set `ALLOW_DANGEROUS=true` to enable them.

secrets in responses are automatically redacted.

## testing

```bash
python test_reflection.py
python test_safety.py
```

## example

```bash
# start server
python server.py

# send request
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python server.py
```

## architecture

```
server.py          - main server loop
mcp_protocol.py    - mcp json-rpc handling
reflection.py      - method discovery
schema_gen.py      - schema generation
auth.py            - authentication injection
safety.py          - safety checks and redaction
pagination.py      - pagination detection
```

## current limitations

- auth only works for a few sdks
- pagination handling is basic
- error messages could be better
- no retry logic yet
- limited test coverage

## todo

- add more auth providers
- better pagination support
- add timeout handling
- retry logic for failures
- more comprehensive tests
- better documentation

## notes

work in progress. core functionality is there but needs polish.
