# setup instructions

## 1. install dependencies

```bash
pip install -r requirements.txt
```

## 2. configure credentials

```bash
cd demo_agent
cp .env.example .env
```

edit the `.env` file with your credentials:

```bash
# required
OPENAI_API_KEY=sk-...

# optional - only add if testing these sdks
GITHUB_TOKEN=ghp_...
AZURE_TENANT_ID=...
AZURE_SUBSCRIPTION_ID=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
STRIPE_API_KEY=sk_test_...
```

### getting credentials

**openai** (required)
- get your api key from https://platform.openai.com/api-keys

**github** (optional)
- create token at https://github.com/settings/tokens
- needs `repo` scope for repository access

**azure** (optional)
- tenant id: found in azure portal -> azure active directory -> properties
- subscription id: azure portal -> subscriptions
- requires azure cli login: `az login`

**aws** (optional)
- create access keys in iam console: https://console.aws.amazon.com/iam/
- or use `aws configure` cli command

**stripe** (optional)
- get test api key from https://dashboard.stripe.com/test/apikeys

**kubernetes** (optional)
- uses `~/.kube/config` automatically
- if you have kubectl configured, it will work
- no environment variables needed

## 3. run the demo

```bash
# from demo_agent directory
python app.py

# or use the run script
./run.sh
```

## 4. test core functionality (without openai)

```bash
cd core_sdk_to_mcp_tool
python test_core_functionality.py
```

this tests the sdk-to-mcp conversion without requiring any api keys.

## troubleshooting

**modulenotfounderror: no module named 'textual'**
- run: `pip install -r requirements.txt`
- make sure you're using the same python that installed packages

**sdk not loading / no methods found**
- check that the sdk is installed: `pip list | grep <sdk-name>`
- for complex sdks (kubernetes, azure, github), credentials may be required

**authentication errors**
- verify credentials in `.env` file
- for azure: run `az login` first
- for kubernetes: verify `kubectl get pods` works
- for github: check token has correct scopes

**openai api errors**
- verify api key is correct in `.env`
- check you have credits at https://platform.openai.com/usage

