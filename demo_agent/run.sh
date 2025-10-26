#!/bin/bash
# run script for mcp sdk agent demo

# check if .env file exists
if [ ! -f ".env" ]; then
    echo "error: .env file not found"
    echo "please run: cp .env.example .env"
    echo "then edit .env and add your OPENAI_API_KEY"
    exit 1
fi

# check if openai api key is set in .env
if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=your-openai-api-key-here" .env; then
    echo "error: OPENAI_API_KEY not configured in .env"
    echo "please edit .env and add your api key"
    exit 1
fi

# check if server.py exists in parent directory
if [ ! -f "../server.py" ]; then
    echo "error: server.py not found in parent directory"
    echo "make sure you're running from demo_agent/ directory"
    exit 1
fi

# check if dependencies are installed
python3 -c "import textual" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "error: textual not installed"
    echo "please run: pip install -r requirements.txt"
    exit 1
fi

python3 -c "import openai" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "error: openai not installed"
    echo "please run: pip install -r requirements.txt"
    exit 1
fi

# all checks passed, run the app
echo "starting mcp sdk agent..."
python3 app.py

