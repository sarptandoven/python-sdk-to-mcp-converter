# python sdk to mcp converter

early prototype for converting python sdks into mcp servers.

## what it does

takes any python module and exposes its methods as mcp tools. the server uses reflection to discover methods and generates json schemas automatically.

## current status

basic working prototype. can discover methods from python modules and serve them via mcp protocol over stdio.

## how to run

```bash
python server.py
```

then send mcp requests via stdin:

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
```

## what works

- discovers functions and class methods from modules
- generates basic json schemas from type hints
- handles tools/list and tools/call
- stdio transport

## todo

- add authentication support
- handle pagination
- better error handling
- add tests
- support more sdks

## example

```bash
# start server
python server.py

# in another terminal, test it
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}' | python server.py
```

## architecture

```
server.py          - main server loop
mcp_protocol.py    - handles mcp json-rpc
reflection.py      - discovers methods
schema_gen.py      - generates schemas
```

## notes

this is an early version. many features still needed but the core concept works.

