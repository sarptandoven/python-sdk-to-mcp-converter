# terminal ui for mcp sdk agent with openai
# interface for devops/infrastructure management

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.widgets import (
    Header, Footer, Input, Static, Button, 
    Select, Label, TabbedContent, TabPane,
    DataTable, LoadingIndicator
)
from textual.binding import Binding
from textual.reactive import reactive
from textual import events
from rich.text import Text
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table as RichTable
from datetime import datetime
import json
import asyncio
import os
from pathlib import Path

from agent import OpenAIMCPAgent
from config import Config

# Load credentials from .env file if it exists
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                key, value = key.strip(), value.strip()
                if key and value and not os.getenv(key):
                    os.environ[key] = value
    print("[OK] Loaded credentials from .env file")


class StatusBar(Static):
    """real-time status indicator"""
    
    sdk = reactive("none")
    tools_count = reactive(0)
    status = reactive("idle")
    
    def render(self):
        return Text.assemble(
            ("sdk: ", ""),
            (self.sdk, ""),
            (" | ", ""),
            ("tools: ", ""),
            (str(self.tools_count), ""),
            (" | ", ""),
            ("status: ", ""),
            (self.status, "")
        )


class ToolCallDisplay(Static):
    """displays tool calls in real-time"""
    
    def __init__(self, tool_name: str, args: dict, **kwargs):
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.args = args
        self.result = None
        self.error = None
        self.start_time = datetime.now()
        self.end_time = None
        
    def render(self):
        if self.error:
            return Panel(
                Text.assemble(
                    ("tool: ", ""),
                    (self.tool_name, ""),
                    ("\nerror: ", ""),
                    (str(self.error), ""),
                ),
                border_style="dim",
                title=f"{self._duration()}"
            )
        elif self.result is not None:
            result_preview = self._format_result(self.result)
            return Panel(
                Text.assemble(
                    ("tool: ", ""),
                    (self.tool_name, ""),
                    ("\nargs: ", ""),
                    (json.dumps(self.args, indent=2), ""),
                    ("\nresult: ", ""),
                    (result_preview, ""),
                ),
                border_style="dim",
                title=f"{self._duration()}"
            )
        else:
            return Panel(
                Text.assemble(
                    ("tool: ", ""),
                    (self.tool_name, ""),
                    ("\nargs: ", ""),
                    (json.dumps(self.args, indent=2), ""),
                    ("\nrunning...", ""),
                ),
                border_style="dim",
                title=f"{self._duration()}"
            )
    
    def _duration(self):
        end = self.end_time or datetime.now()
        delta = end - self.start_time
        return f"{delta.total_seconds():.2f}s"
    
    def _format_result(self, result):
        """format result for display"""
        if result is None:
            return "None"
        
        result_str = str(result)
        if len(result_str) > 500:
            return result_str[:500] + f"\n... (truncated, total {len(result_str)} chars)"
        return result_str
    
    def set_result(self, result):
        self.result = result
        self.end_time = datetime.now()
        self.refresh()
    
    def set_error(self, error):
        self.error = error
        self.end_time = datetime.now()
        self.refresh()


class ChatMessage(Static):
    """single chat message"""
    
    def __init__(self, role: str, content: str, **kwargs):
        super().__init__(**kwargs)
        self.role = role
        self.content = content
        self.timestamp = datetime.now().strftime("%H:%M:%S")
        
    def render(self):
        if self.role == "user":
            return Panel(
                Text(self.content, style=""),
                border_style="dim",
                title=f"you [{self.timestamp}]",
                title_align="left"
            )
        elif self.role == "assistant":
            return Panel(
                Text(self.content, style=""),
                border_style="dim",
                title=f"agent [{self.timestamp}]",
                title_align="left"
            )
        else:  # system
            return Panel(
                Text(self.content, style="dim"),
                border_style="dim",
                title=f"system [{self.timestamp}]",
                title_align="left"
            )


class ToolBrowser(Static):
    """browse available tools"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools = []
        
    def compose(self) -> ComposeResult:
        self.table = DataTable()
        self.table.add_columns("Tool Name", "Description")
        yield self.table
        
    def set_tools(self, tools):
        self.tools = tools
        self.table.clear()
        
        # show first 100 tools
        for tool in tools[:100]:
            name = tool.get("name", "unknown")
            desc = tool.get("description", "no description")
            if len(desc) > 60:
                desc = desc[:60] + "..."
            self.table.add_row(name, desc)
        
        if len(tools) > 100:
            self.table.add_row(
                f"... and {len(tools) - 100} more",
                "use search to find specific tools"
            )


class SDKPanel(Static):
    """sdk configuration panel"""
    
    def compose(self) -> ComposeResult:
        yield Label("Select SDK:", classes="label")
        yield Select(
            [
                ("os (Python standard library)", "os"),
                ("json (Python standard library)", "json"),
                ("pathlib (Path operations)", "pathlib"),
                ("requests (HTTP library)", "requests"),
                ("kubernetes (K8s client)", "kubernetes"),
                ("github (PyGithub)", "github"),
                ("boto3 (AWS SDK)", "boto3"),
                ("azure.mgmt.resource (Azure Resources)", "azure.mgmt.resource"),
                ("azure.mgmt.compute (Azure Compute)", "azure.mgmt.compute"),
                ("stripe (Stripe API)", "stripe"),
                ("custom...", "custom")
            ],
            id="sdk_select",
            prompt="Choose an SDK",
            value="os"
        )
        yield Input(placeholder="enter custom sdk name (e.g. numpy)", id="custom_sdk_input", classes="hidden")
        yield Button("Load SDK", id="load_sdk", variant="primary")
        yield Static("click 'Load SDK' to start", id="sdk_status")


class ExamplesPanel(Static):
    """example queries for quick start"""
    
    EXAMPLES = {
        "os": [
            "what is my current working directory?",
            "how many cpu cores does this machine have?",
            "what are my environment variables?",
            "what operating system am I running?",
            "check the current user home directory",
        ],
        "json": [
            "encode this dict to json: {'name': 'test', 'value': 123}",
            "parse this json string: '{\"key\": \"value\"}'",
            "what json tools are available?",
        ],
        "pathlib": [
            "get the absolute path of this directory",
            "check if a file exists",
            "list all python files here",
        ],
        "kubernetes": [
            "list pods in default namespace",
            "show all namespaces",
            "get nodes in the cluster",
            "describe services in kube-system",
            "check deployment status",
        ],
        "github": [
            "NOTE: Load 'os' SDK for filesystem operations",
            "show my repositories",
            "list issues in a repo",
            "get pull requests",
            "check workflows",
        ],
        "azure.mgmt.resource": [
            "NOTE: Requires Azure credentials (already in .env!)",
            "list resource groups",
            "show resources in subscription",
            "get resource group details",
        ],
        "azure.mgmt.compute": [
            "NOTE: Requires Azure credentials (already in .env!)",
            "list virtual machines",
            "show VM sizes",
            "get VM details",
        ],
        "boto3": [
            "NOTE: Requires AWS credentials",
            "list s3 buckets",
            "describe ec2 instances",
            "check lambda functions",
        ],
        "stripe": [
            "NOTE: Requires Stripe API key",
            "list customers",
            "get payment intents",
            "check subscriptions",
        ]
    }
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_sdk = "os"  # default to os
        
    def render(self):
        examples = self.EXAMPLES.get(self.current_sdk, [])
        
        if not examples:
            return Panel(
                "load sdk for examples",
                border_style="dim",
                title="examples"
            )
        
        content = "\n".join([f"{i+1}. {ex}" for i, ex in enumerate(examples)])
        return Panel(
            content,
            border_style="dim",
            title="examples"
        )
    
    def set_sdk(self, sdk: str):
        self.current_sdk = sdk
        self.refresh()


class MCPAgentTUI(App):
    """
    production-grade terminal ui for mcp sdk agent
    
    features:
    - dynamic sdk loading
    - real-time chat interface
    - tool call visualization
    - tool browsing
    - keyboard shortcuts
    - example queries
    - status tracking
    """
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main_container {
        layout: horizontal;
        height: 100%;
    }
    
    #left_sidebar {
        width: 30;
        background: $panel;
        border-right: solid $primary;
    }
    
    #center_chat {
        width: 1fr;
        background: $surface;
    }
    
    #right_sidebar {
        width: 40;
        background: $panel;
        border-left: solid $primary;
    }
    
    #status_bar {
        dock: top;
        height: 1;
        background: $primary;
        color: $text;
        padding: 0 1;
    }
    
    #chat_container {
        height: 1fr;
        background: $surface;
        padding: 1;
    }
    
    #input_container {
        dock: bottom;
        height: 3;
        background: $panel;
        padding: 0 1;
    }
    
    Input {
        width: 100%;
    }
    
    Button {
        margin: 1 0;
    }
    
    .label {
        margin: 1 0 0 0;
        color: $text-muted;
    }
    
    .hidden {
        display: none;
    }
    
    DataTable {
        height: 100%;
    }
    
    TabbedContent {
        height: 100%;
    }
    
    #sdk_status {
        margin: 1 0;
        color: $text;
    }
    
    #custom_sdk_input {
        margin: 1 0;
    }
    """
    
    BINDINGS = [
        Binding("ctrl+q", "quit", "quit", show=True),
        Binding("ctrl+l", "clear", "clear chat", show=True),
        Binding("ctrl+s", "toggle_sidebar", "toggle sidebar", show=False),
        Binding("ctrl+t", "toggle_tools", "toggle tools", show=False),
        Binding("ctrl+e", "show_examples", "examples", show=True),
    ]
    
    TITLE = "mcp sdk agent"
    
    def __init__(self):
        super().__init__()
        self.agent = None
        self.config = Config()
        self.current_sdk = "os"  # default to os
        self.conversation_history = []
        
    def compose(self) -> ComposeResult:
        """build the ui"""
        yield Header()
        
        with Container(id="main_container"):
            # left sidebar: sdk config + examples
            with Vertical(id="left_sidebar"):
                yield SDKPanel()
                yield ExamplesPanel()
            
            # center: chat interface
            with Vertical(id="center_chat"):
                yield StatusBar(id="status_bar")
                yield ScrollableContainer(id="chat_container")
                with Container(id="input_container"):
                    yield Input(
                        placeholder="ask me to manage your infrastructure...",
                        id="user_input"
                    )
            
            # right sidebar: tool browser and info
            with Vertical(id="right_sidebar"):
                with TabbedContent():
                    with TabPane("Tools", id="tools_tab"):
                        yield ToolBrowser()
                    with TabPane("Info", id="info_tab"):
                        yield Static(
                            self._render_info(),
                            id="info_content"
                        )
        
        yield Footer()
    
    def _render_info(self):
        """render info panel content"""
        return Panel(
            Text.assemble(
                ("shortcuts:\n", ""),
                ("ctrl+q - quit\n", ""),
                ("ctrl+l - clear\n", ""),
                ("ctrl+e - examples\n", ""),
                ("enter - send\n", ""),
            ),
            border_style="dim",
            title="info"
        )
    
    async def on_mount(self):
        """initialize on startup"""
        # show welcome message
        self.add_system_message(
            "Welcome to MCP SDK Agent!\n\n"
            "This tool lets you interact with any Python SDK using natural language.\n\n"
            "To get started:\n"
            "1. Select an SDK from the left panel (or use the default 'os' module)\n"
            "2. Click 'Load SDK' to initialize\n"
            "3. Type your request in natural language\n\n"
            "Example: 'what is my current directory?' or 'list files in this folder'"
        )
        # focus input
        self.query_one("#user_input").focus()
    
    async def on_button_pressed(self, event: Button.Pressed):
        """handle button clicks"""
        if event.button.id == "load_sdk":
            await self.load_sdk()
    
    async def on_select_changed(self, event: Select.Changed):
        """handle sdk selection"""
        if event.select.id == "sdk_select":
            self.current_sdk = event.value
            # show/hide custom input based on selection
            custom_input = self.query_one("#custom_sdk_input", Input)
            if event.value == "custom":
                custom_input.remove_class("hidden")
            else:
                custom_input.add_class("hidden")
    
    async def on_input_submitted(self, event: Input.Submitted):
        """handle user input"""
        if event.input.id == "user_input":
            message = event.value.strip()
            if not message:
                return
            
            # clear input
            event.input.value = ""
            
            # check if agent is loaded
            if not self.agent:
                self.add_system_message("load sdk first")
                return
            
            # process message
            await self.process_message(message)
    
    async def load_sdk(self):
        """load selected sdk"""
        # update current_sdk from select widget if needed
        select_widget = self.query_one("#sdk_select", Select)
        if select_widget.value != Select.BLANK:
            self.current_sdk = select_widget.value
        
        if not self.current_sdk:
            self.add_system_message("select sdk first")
            return
        
        # handle custom sdk
        sdk_to_load = self.current_sdk
        if self.current_sdk == "custom":
            custom_input = self.query_one("#custom_sdk_input", Input)
            custom_sdk = custom_input.value.strip()
            if not custom_sdk:
                self.add_system_message("enter custom sdk name")
                return
            sdk_to_load = custom_sdk
        
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.status = "loading"
        
        try:
            self.add_system_message(f"loading {sdk_to_load}...")
            
            # create agent
            self.agent = OpenAIMCPAgent(
                sdk_name=sdk_to_load,
                openai_api_key=self.config.openai_api_key
            )
            
            # initialize (spawns mcp server, fetches tools)
            self.add_system_message(f"initializing MCP server for {sdk_to_load}...")
            await self.agent.initialize()
            
            # update ui
            status_bar.sdk = sdk_to_load
            status_bar.tools_count = len(self.agent.tools)
            status_bar.status = "ready"
            
            # update tool browser
            tool_browser = self.query_one(ToolBrowser)
            tool_browser.set_tools(self.agent.tools)
            
            # update examples
            examples = self.query_one(ExamplesPanel)
            examples.set_sdk(sdk_to_load)
            
            # update sdk status
            sdk_status = self.query_one("#sdk_status")
            sdk_status.update(
                f"[OK] {len(self.agent.tools)} tools ready"
            )
            
            # Get first few tool names as examples
            tool_samples = [t['function']['name'].replace('_', '.') for t in self.agent.tools[:3]]
            tool_sample_str = ", ".join(tool_samples)
            
            # SDK-specific guidance
            sdk_notes = {
                "os": "try: 'what is my current directory?' or 'how many cpu cores?'",
                "json": "try: 'encode this to json: {\"test\": 123}'",
                "kubernetes": "try: 'list pods in default namespace'",
                "github": "try: 'show my repositories'",
                "boto3": "try: 'list s3 buckets' (needs AWS credentials)",
                "azure.mgmt.resource": "try: 'list resource groups' (credentials in .env!)",
                "azure.mgmt.compute": "try: 'list virtual machines' (credentials in .env!)",
                "stripe": "try: 'list customers' (needs Stripe API key)"
            }
            
            suggestion = sdk_notes.get(sdk_to_load, f"example tools: {tool_sample_str}")
            
            # Check if tools were truncated due to OpenAI's 128 tool limit
            truncation_warning = ""
            if self.agent.tools_truncated > 0:
                truncation_warning = (
                    f"\n[WARN] WARNING: OpenAI limits agents to 128 tools maximum.\n"
                    f"   This SDK has {len(self.agent.tools) + self.agent.tools_truncated} tools total.\n"
                    f"   Only the first 128 tools are loaded. ({self.agent.tools_truncated} tools not available)\n"
                )
            
            self.add_system_message(
                f"[OK] successfully loaded {sdk_to_load}\n"
                f"   discovered {len(self.agent.tools)} tools\n"
                f"   ready for {sdk_to_load}-specific operations\n"
                f"{truncation_warning}\n"
                f"{suggestion}\n\n"
                f"note: each SDK has specific tools - load the right SDK for your task!"
            )
            
        except Exception as e:
            status_bar.status = "error"
            sdk_status = self.query_one("#sdk_status")
            sdk_status.update(f"[FAIL] error loading SDK")
            
            error_msg = str(e)
            if "ModuleNotFoundError" in error_msg or "No module named" in error_msg:
                self.add_system_message(
                    f"error: SDK '{sdk_to_load}' not installed\n\n"
                    f"install it with:\n"
                    f"  pip install {sdk_to_load}"
                )
            elif "authentication" in error_msg.lower() or "auth" in error_msg.lower():
                self.add_system_message(
                    f"error: authentication required\n\n"
                    f"set up credentials for {sdk_to_load} first"
                )
            else:
                self.add_system_message(f"error loading SDK: {error_msg}")
    
    async def process_message(self, message: str):
        """process user message with agent"""
        # add user message
        self.add_chat_message("user", message)
        
        # update status
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.status = "thinking"
        
        try:
            # call openai
            response = await self.agent.process(
                message,
                on_tool_call=self.on_tool_call
            )
            
            # add response
            self.add_chat_message("assistant", response)
            
            status_bar.status = "success"
            
        except Exception as e:
            self.add_system_message(f"error: {str(e)}")
            status_bar.status = "error"
        
        finally:
            # reset to idle after 2 seconds
            await asyncio.sleep(2)
            status_bar.status = "idle"
    
    async def on_tool_call(self, tool_name: str, arguments: dict):
        """callback when agent calls a tool"""
        status_bar = self.query_one("#status_bar", StatusBar)
        status_bar.status = "calling"
        
        # create tool call display
        tool_display = ToolCallDisplay(tool_name, arguments)
        
        # add to chat
        chat_container = self.query_one("#chat_container")
        await chat_container.mount(tool_display)
        
        # scroll to bottom
        chat_container.scroll_end(animate=False)
        
        return tool_display
    
    def add_chat_message(self, role: str, content: str):
        """add message to chat"""
        chat_container = self.query_one("#chat_container")
        message = ChatMessage(role, content)
        self.call_later(chat_container.mount, message)
        self.call_later(chat_container.scroll_end)
        
        # add to history
        self.conversation_history.append({"role": role, "content": content})
    
    def add_system_message(self, content: str):
        """add system message"""
        self.add_chat_message("system", content)
    
    def action_clear(self):
        """clear chat"""
        chat_container = self.query_one("#chat_container")
        chat_container.remove_children()
        self.conversation_history = []
        self.add_system_message("chat cleared")
    
    def action_show_examples(self):
        """show examples in chat"""
        if not self.current_sdk:
            self.add_system_message("load an sdk first to see examples")
            return
        
        examples = ExamplesPanel.EXAMPLES.get(self.current_sdk, [])
        if examples:
            content = "example queries you can try:\n\n" + "\n".join(
                [f"{i+1}. {ex}" for i, ex in enumerate(examples)]
            )
            self.add_system_message(content)


if __name__ == "__main__":
    app = MCPAgentTUI()
    app.run()

