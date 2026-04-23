from __future__ import annotations

from pathlib import Path

from mcp.server.fastmcp import FastMCP

from .demo import run_demo
from .runtime import (
    DEFAULT_DB_PATH,
    build_debrief_submission,
    build_match_context,
    build_service,
)


def _service_for(db_path: str | None):
    return build_service(Path(db_path) if db_path else DEFAULT_DB_PATH)


def build_server() -> FastMCP:
    server = FastMCP(
        "Afterglow",
        instructions=(
            "Afterglow is a post-date learning harness for Ditto-style systems. "
            "Use these tools to register dates, open tiny check-ins, ingest debriefs, "
            "finalize outcomes, inspect traces, and read ranking memory."
        ),
    )

    @server.tool(description="Health check for the Afterglow integration surface.")
    def health(db_path: str | None = None) -> dict[str, str]:
        _service_for(db_path)
        return {"status": "ok"}

    @server.tool(description="Register a completed match so Afterglow can learn from it.")
    def register_match(
        match_id: str,
        user_a_id: str,
        user_b_id: str,
        venue_name: str,
        completed_at: str = "now",
        db_path: str | None = None,
    ) -> dict[str, object]:
        service = _service_for(db_path)
        return service.register_match(
            build_match_context(
                match_id=match_id,
                user_a_id=user_a_id,
                user_b_id=user_b_id,
                venue_name=venue_name,
                completed_at=completed_at,
            )
        )

    @server.tool(description="Queue the tiny post-date check-in messages for both participants.")
    def open_check_in(match_id: str, db_path: str | None = None) -> dict[str, object]:
        return _service_for(db_path).open_check_in_window(match_id)

    @server.tool(description="Submit one structured participant debrief.")
    def submit_debrief(
        match_id: str,
        user_id: str,
        date_rating: int,
        energy: str,
        curiosity: str,
        comfort: str,
        follow_up_intent: str,
        note: str = "",
        db_path: str | None = None,
    ) -> dict[str, object]:
        return _service_for(db_path).submit_debrief(
            build_debrief_submission(
                match_id=match_id,
                user_id=user_id,
                date_rating=date_rating,
                energy=energy,
                curiosity=curiosity,
                comfort=comfort,
                follow_up_intent=follow_up_intent,
                note=note,
            )
        )

    @server.tool(description="Receive an SMS-style reply and normalize it into a debrief submission.")
    def receive_sms(
        match_id: str,
        user_id: str,
        rating: int,
        energy: str,
        curiosity: str,
        comfort: str,
        follow_up_intent: str,
        note: str = "",
        db_path: str | None = None,
    ) -> dict[str, object]:
        return _service_for(db_path).receive_sms_reply(
            {
                "match_id": match_id,
                "user_id": user_id,
                "rating": rating,
                "energy": energy,
                "curiosity": curiosity,
                "comfort": comfort,
                "follow_up_intent": follow_up_intent,
                "note": note,
            }
        )

    @server.tool(description="Finalize a match explicitly, usually after a timeout.")
    def finalize_match(match_id: str, reason: str = "timeout", db_path: str | None = None) -> dict[str, object]:
        return _service_for(db_path).finalize_match(match_id, reason=reason)

    @server.tool(description="Fetch the current summary for one match.")
    def get_match(match_id: str, db_path: str | None = None) -> dict[str, object]:
        return _service_for(db_path).get_match_summary(match_id)

    @server.tool(description="Fetch the internal reasoning trace for one match.")
    def get_trace(match_id: str, db_path: str | None = None) -> list[dict[str, object]]:
        return _service_for(db_path).get_trace(match_id)

    @server.tool(description="List outbound SMS work queued for the texting provider.")
    def list_outbox(
        match_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        db_path: str | None = None,
    ) -> list[dict[str, object]]:
        return _service_for(db_path).list_check_in_messages(match_id=match_id, status=status, limit=limit)

    @server.tool(description="Mark one queued message as sent by the provider.")
    def mark_sent(
        message_id: int,
        provider_message_id: str | None = None,
        provider_status: str | None = None,
        db_path: str | None = None,
    ) -> dict[str, object]:
        return _service_for(db_path).mark_check_in_message_sent(
            message_id,
            provider_message_id=provider_message_id,
            provider_status=provider_status,
        )

    @server.tool(description="Fetch global ranking memory derived from date outcomes.")
    def get_global_memory(db_path: str | None = None) -> dict[str, object]:
        return _service_for(db_path).get_global_memory_snapshot()

    @server.tool(description="Run the built-in happy-path demo for quick verification.")
    def demo(db_path: str | None = None, keep_db: bool = False) -> dict[str, object]:
        return run_demo(db_path=Path(db_path) if db_path else DEFAULT_DB_PATH, keep_db=keep_db)

    return server


def main() -> None:
    build_server().run(transport="stdio")


if __name__ == "__main__":
    main()
