"""Twenty CRM Plugin for Hermes Agent.

Provides deep integration with Twenty CRM:
- TwentyClient for REST API interactions (people, companies, opportunities, notes, tasks, webhooks)
- AutonomousDealLoop for autonomous note logging, local Chinese LLM summarization, and task scheduling
- CLI tooling under `hermes twenty`
"""

from .autonomous_loop import AutonomousDealLoop
from .client import TwentyClient
from .cli import run_twenty_cli, create_twenty_parser
from .composio_fabric import ComposioFabric

__all__ = [
    "TwentyClient",
    "AutonomousDealLoop",
    "ComposioFabric",
    "run_twenty_cli",
    "create_twenty_parser",
]
