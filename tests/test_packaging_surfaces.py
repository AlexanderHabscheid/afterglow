from __future__ import annotations

import asyncio
import contextlib
import io
import json
import sys
import tempfile
import unittest
from unittest.mock import patch

from afterglow.cli import main as cli_main
from afterglow.mcp_server import build_server


class PackagingSurfaceTests(unittest.TestCase):
    def test_cli_register_and_read_match(self) -> None:
        with tempfile.NamedTemporaryFile(suffix=".db") as temp_db:
            register_stdout = io.StringIO()
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "afterglow",
                        "--db-path",
                        temp_db.name,
                        "register-match",
                        "--match-id",
                        "match-cli-001",
                        "--user-a-id",
                        "avery",
                        "--user-b-id",
                        "lena",
                        "--venue-name",
                        "Campanile sunset loop",
                        "--completed-at",
                        "2026-04-21T17:30:00+00:00",
                    ],
                ),
                contextlib.redirect_stdout(register_stdout),
            ):
                cli_main()

            match_stdout = io.StringIO()
            with (
                patch.object(
                    sys,
                    "argv",
                    [
                        "afterglow",
                        "--db-path",
                        temp_db.name,
                        "get-match",
                        "--match-id",
                        "match-cli-001",
                    ],
                ),
                contextlib.redirect_stdout(match_stdout),
            ):
                cli_main()

            registered = json.loads(register_stdout.getvalue())
            fetched = json.loads(match_stdout.getvalue())
            self.assertEqual(registered["status"], "registered")
            self.assertEqual(fetched["match_id"], "match-cli-001")
            self.assertEqual(fetched["submission_count"], 0)

    def test_mcp_tools_are_callable(self) -> None:
        async def exercise() -> None:
            with tempfile.NamedTemporaryFile(suffix=".db") as temp_db:
                server = build_server()
                tools = await server.list_tools()
                tool_names = {tool.name for tool in tools}
                self.assertIn("register_match", tool_names)
                self.assertIn("open_check_in", tool_names)

                _, registered = await server.call_tool(
                    "register_match",
                    {
                        "match_id": "match-mcp-001",
                        "user_a_id": "avery",
                        "user_b_id": "lena",
                        "venue_name": "Campanile sunset loop",
                        "completed_at": "2026-04-21T17:30:00+00:00",
                        "db_path": temp_db.name,
                    },
                )
                _, queued = await server.call_tool(
                    "open_check_in",
                    {"match_id": "match-mcp-001", "db_path": temp_db.name},
                )
                self.assertEqual(registered["status"], "registered")
                self.assertEqual(queued["status"], "check-in-open")
                self.assertEqual(len(queued["queued_messages"]), 2)

        asyncio.run(exercise())


if __name__ == "__main__":
    unittest.main()
