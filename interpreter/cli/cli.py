import argparse
import json
import subprocess
import os
import platform
import time
import pkg_resources
import appdirs
from ..utils.display_markdown_message import display_markdown_message
from ..terminal_interface.conversation_navigator import conversation_navigator

arguments = [
    {
        "name": "system_message",
        "nickname": "s",
        "help_text": "prompt / custom instructions for the language model",
        "type": str
    },
    {
        "name": "local",
        "nickname": "l",
        "help_text": "run in local mode",
        "type": bool
    },
    {
        "name": "auto_run",
        "nickname": "y",
        "help_text": "automatically run the interpreter",
        "type": bool
    },
    {
        "name": "debug_mode",
        "nickname": "d",
        "help_text": "run in debug mode",
        "type": bool
    },
    {
        "name": "model",
        "nickname": "m",
        "help_text": "model to use for the language model",
        "type": str
    },
    {
        "name": "temperature",
        "nickname": "t",
        "help_text": "optional temperature setting for the language model",
        "type": float
    },
    {
        "name": "context_window",
        "nickname": "c",
        "help_text": "optional context window size for the language model",
        "type": int
    },
    {
        "name": "max_tokens",
        "nickname": "x",
        "help_text": "optional maximum number of tokens for the language model",
        "type": int
    },
    {
        "name": "max_budget",
        "nickname": "b",
        "help_text": "optionally set the max budget (in USD) for your llm calls",
        "type": float
    },
    {
        "name": "api_base",
        "nickname": "ab",
        "help_text": "optionally set the API base URL for your llm calls (this will override environment variables)",
        "type": str
    },
    {
        "name": "api_key",
        "nickname": "ak",
        "help_text": "optionally set the API key for your llm calls (this will override environment variables)",
        "type": str
    },
    {
        "name": "safe_mode",
        "nickname": "safe",
        "help_text": "optionally enable safety mechanisms like code scanning; valid options are off, ask, and auto",
        "type": str,
        "choices": ["off", "ask", "auto"]
    }
]

def cli(interpreter):

    parser = argparse.ArgumentParser(description="open-mind")
    subparsers = parser.add_subparsers(dest="command")

    # Induction subcommands
    induce_parser = subparsers.add_parser("induce", help="Ingest a GitHub repo and build vector models")
    induce_parser.add_argument("repo_url", help="GitHub repository URL")
    induce_parser.add_argument("--target-dir", help="Local directory to clone into", default=None)
    induce_parser.add_argument("--cleanup", action="store_true", help="Remove cloned repo after ingestion")
    induce_parser.add_argument("--verbose", "-v", action="store_true", help="Print detailed results")

    spread_parser = subparsers.add_parser("spread", help="Start continuous spreading on a repo")
    spread_parser.add_argument("repo_url", help="GitHub repository URL")
    spread_parser.add_argument("--passes", type=int, default=5, help="Number of spreading passes (default: 5)")
    spread_parser.add_argument("--target-dir", help="Local directory to clone into", default=None)

    status_parser = subparsers.add_parser("inspector", help="Show induction state")
    status_parser.add_argument("--repo", help="Repo URL to inspect", default=None)

    # Add arguments
    for arg in arguments:
        if arg["type"] == bool:
            parser.add_argument(f'-{arg["nickname"]}', f'--{arg["name"]}', dest=arg["name"], help=arg["help_text"], action='store_true', default=None)
        else:
            choices = arg["choices"] if "choices" in arg else None
            default = arg["default"] if "default" in arg else None

            parser.add_argument(f'-{arg["nickname"]}', f'--{arg["name"]}', dest=arg["name"], help=arg["help_text"], type=arg["type"], choices=choices, default=default)

    # Add special arguments
    parser.add_argument('--config', dest='config', action='store_true', help='open config.yaml file in text editor')
    parser.add_argument('--conversations', dest='conversations', action='store_true', help='list conversations to resume')
    parser.add_argument('-f', '--fast', dest='fast', action='store_true', help='(depracated) runs `interpreter --model gpt-3.5-turbo`')
    parser.add_argument('--version', dest='version', action='store_true', help="get Open Interpreter's version number")

    # TODO: Implement model explorer
    # parser.add_argument('--models', dest='models', action='store_true', help='list avaliable models')

    args = parser.parse_args()

    # This should be pushed into an open_config.py util
    # If --config is used, open the config.yaml file in the Open Interpreter folder of the user's config dir
    if args.config:
        config_dir = appdirs.user_config_dir("Open Interpreter")
        config_path = os.path.join(config_dir, 'config.yaml')
        print(f"Opening `{config_path}`...")
        # Use the default system editor to open the file
        if platform.system() == 'Windows':
            os.startfile(config_path)  # This will open the file with the default application, e.g., Notepad
        else:
            try:
                # Try using xdg-open on non-Windows platforms
                subprocess.call(['xdg-open', config_path])
            except FileNotFoundError:
                # Fallback to using 'open' on macOS if 'xdg-open' is not available
                subprocess.call(['open', config_path])
        return
    
    # TODO Implement model explorer
    """
    # If --models is used, list models
    if args.models:
        # If they pick a model, set model to that then proceed
        args.model = model_explorer()
    """

    # Set attributes on interpreter
    for attr_name, attr_value in vars(args).items():
        # Ignore things that aren't possible attributes on interpreter
        if attr_value is not None and hasattr(interpreter, attr_name):
            setattr(interpreter, attr_name, attr_value)

    # if safe_mode and auto_run are enabled, safe_mode disables auto_run
    if interpreter.auto_run and not interpreter.safe_mode == "off":
        setattr(interpreter, "auto_run", False)

    # Default to CodeLlama if --local is on but --model is unset
    if interpreter.local and args.model is None:
        # This will cause the terminal_interface to walk the user through setting up a local LLM
        interpreter.model = ""

    # If --conversations is used, run conversation_navigator
    if args.conversations:
        conversation_navigator(interpreter)
        return
    
    if args.version:
        version = pkg_resources.get_distribution("open-interpreter").version
        print(f"Open Interpreter {version}")
        return
    
    # Depracated --fast
    if args.fast:
        # This will cause the terminal_interface to walk the user through setting up a local LLM
        interpreter.model = "gpt-3.5-turbo"
        print("`interpreter --fast` is depracated and will be removed in the next version. Please use `interpreter --model gpt-3.5-turbo`")

    # Handle induction subcommands
    if args.command == "induce":
        _handle_induce(args)
        return
    elif args.command == "spread":
        _handle_spread(args)
        return
    elif args.command == "inspector":
        _handle_inspector(args)
        return

    interpreter.chat()


def _handle_induce(args):
    """Handle the `interpreter induce` subcommand."""
    from interpreter.induction import ingest as do_ingest

    print(f"\n🧠 Inducing: {args.repo_url}")
    print("   Ingesting repository...")

    result = do_ingest(args.repo_url, target_dir=args.target_dir, cleanup=args.cleanup)

    print(f"\n✅ Ingestion complete!")
    print(f"   Functions: {result.stats['total_functions']}")
    print(f"   Classes: {result.stats['total_classes']}")
    print(f"   Test files: {result.stats['test_files']}")
    print(f"   Tested functions: {result.stats['tested_functions']}")
    print(f"   Python files: {result.stats['python_files']}")

    if args.verbose:
        print(f"\n   Call graph entries: {len(result.call_graph)}")
        print(f"   Top-level modules:")
        for key in sorted(result.file_structure.keys())[:10]:
            print(f"     {key}/ ({len(result.file_structure[key])} files)")


def _handle_spread(args):
    """Handle the `interpreter spread` subcommand."""
    from interpreter.induction import Spreader

    print(f"\n🔄 Spreading: {args.repo_url}")
    print(f"   Running {args.passes} passes...")

    spreader = Spreader(args.repo_url, target_dir=args.target_dir)

    for i in range(1, args.passes + 1):
        print(f"\n   Pass {i}/{args.passes}...", end=" ")
        spreader._run_pass(i)
        spreader.state.current_pass = i
        spreader.state.last_pass_at = time.time()
        spreader._save_state()
        phase = spreader.state.phase.value
        print(f"[{phase}]")

    status = spreader.status()
    print(f"\n✅ Spreading complete!")
    print(f"   Phase: {status['phase']}")
    print(f"   Hot paths: {status['hot_paths']}")
    if status.get('decisions'):
        for decision, count in status['decisions'].items():
            print(f"   {decision}: {count} functions")


def _handle_inspector(args):
    """Handle the `interpreter inspector` subcommand."""
    import glob

    state_dir = os.path.expanduser("~/.open-mind/spreader")

    if args.repo:
        safe_name = args.repo.replace("/", "_").replace(":", "_")
        state_file = os.path.join(state_dir, f"{safe_name}.json")
        if not os.path.exists(state_file):
            print(f"No state found for {args.repo}")
            return
        with open(state_file) as f:
            data = json.load(f)
        print(f"\n📊 Inspector: {args.repo}")
        for key, value in data.items():
            print(f"   {key}: {value}")
    else:
        # List all known repos
        state_files = glob.glob(os.path.join(state_dir, "*.json"))
        if not state_files:
            print("No induction state found. Run `interpreter induce <repo_url>` first.")
            return
        print("\n📊 Known repos:")
        for sf in state_files:
            with open(sf) as f:
                data = json.load(f)
            phase = data.get("phase", "unknown")
            passes = f"{data.get('current_pass', 0)}/{data.get('total_passes', 0)}"
            print(f"   {data.get('repo_url', os.path.basename(sf))} [{phase}] pass {passes}")