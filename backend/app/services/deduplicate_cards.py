import sys
sys.path.insert(0, r"d:\learnSync")
import logging
import re
from uuid import UUID
from typing import Dict, Any, List
from backend.app.core.supabase import SupabaseVectorClient
from backend.app.services.fsrs_engine import review_session_engine

logger = logging.getLogger(__name__)


def purge_duplicate_cards(dry_run: bool = False) -> Dict[str, Any]:
    """
    Scans the Supabase flashcards table for duplicate cards having identical front text
    in the same folder. Keeps the best record (highest reps or latest updated_at) and
    deletes all duplicate copies.
    """
    sb = SupabaseVectorClient()
    if not sb.client:
        return {"status": "error", "message": "Supabase client unavailable"}

    res = sb.client.table("flashcards").select("id, folder_id, user_id, document_id, topic, front, reps, updated_at, created_at").execute()
    cards = res.data or []
    
    # Group by (folder_id, normalized_front)
    grouped: Dict[tuple, List[Dict[str, Any]]] = {}
    for c in cards:
        fid = str(c.get("folder_id") or "")
        front_norm = re.sub(r"[^\w\s]", "", str(c.get("front") or "").strip().lower())
        key = (fid, front_norm)
        grouped.setdefault(key, []).append(c)

    deleted_ids = []
    kept_ids = []

    for key, group in grouped.items():
        if len(group) <= 1:
            if group:
                kept_ids.append(group[0]["id"])
            continue

        # Sort: prefer cards with highest reps, then most recent updated_at
        group.sort(key=lambda x: (int(x.get("reps") or 0), str(x.get("updated_at") or "")), reverse=True)
        keeper = group[0]
        duplicates = group[1:]

        kept_ids.append(keeper["id"])
        for d in duplicates:
            deleted_ids.append(d["id"])
            if not dry_run:
                try:
                    sb.client.table("flashcards").delete().eq("id", d["id"]).execute()
                except Exception as e:
                    logger.warning(f"Failed to delete duplicate card {d['id']}: {e}")

    logger.info(f"Deduplication complete: kept {len(kept_ids)}, deleted {len(deleted_ids)} duplicate cards.")
    return {
        "status": "success",
        "total_cards_scanned": len(cards),
        "cards_kept": len(kept_ids),
        "duplicates_purged": len(deleted_ids),
        "purged_ids": deleted_ids,
    }


def refresh_matchwise_deck() -> Dict[str, Any]:
    """
    Specifically regenerates flashcards for Matchwise-Prism-MW-9842-AX.txt
    to ensure full concept coverage without generic template stubs.
    """
    sb = SupabaseVectorClient()
    if not sb.client:
        return {"status": "error", "message": "No client"}

    doc_res = sb.client.table("documents").select("*").ilike("file_name", "%Matchwise%").execute()
    if not doc_res.data:
        return {"status": "error", "message": "Matchwise document not found"}

    doc = doc_res.data[0]
    doc_id = UUID(doc["id"])
    folder_id = UUID(doc["folder_id"])
    user_id = UUID(doc["user_id"])
    topic = "Matchwise Prism MW 9842 AX"

    # Purge any existing cards for this folder/document first
    try:
        sb.client.table("flashcards").delete().eq("folder_id", str(folder_id)).execute()
    except Exception as e:
        logger.warning(f"Failed to purge existing cards for folder {folder_id}: {e}")

    # Trigger comprehensive handoff generation
    result = review_session_engine.schedule_handoff(
        user_id=user_id,
        folder_id=folder_id,
        topic=topic,
        document_id=doc_id,
        force_regenerate=True,
    )

    return {
        "status": "success",
        "document_id": str(doc_id),
        "folder_id": str(folder_id),
        "cards_scheduled": result.cards_scheduled,
        "message": result.message,
    }


if __name__ == "__main__":
    import sys
    sys.path.insert(0, r"d:\learnSync")
    logging.basicConfig(level=logging.INFO)
    print("Running deduplication...")
    dedup_res = purge_duplicate_cards()
    print("Dedup result:", dedup_res)
    print("Refreshing Matchwise deck...")
    refresh_res = refresh_matchwise_deck()
    print("Refresh result:", refresh_res)
