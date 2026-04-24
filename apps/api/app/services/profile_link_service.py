import uuid
from collections.abc import Iterable
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.profile_link import ProfileLink


def normalize_link_url(url: str) -> str:
    normalized = url.strip().rstrip(".,;")
    if not normalized:
        return ""
    if normalized.startswith(("http://", "https://", "mailto:")):
        return normalized
    lowered = normalized.lower()
    if "@" in normalized and "://" not in normalized and "/" not in normalized:
        return normalized
    if any(host in lowered for host in ("linkedin.com", "github.com", "gitlab.com", "behance.net", "dribbble.com", "medium.com", "substack.com")):
        return f"https://{normalized}"
    if "." in normalized and " " not in normalized:
        return f"https://{normalized}"
    return normalized


def infer_link_type(url: str) -> str:
    lowered = normalize_link_url(url).strip().lower()
    if not lowered:
        return "other"
    if lowered.startswith("mailto:") or ("@" in lowered and "://" not in lowered and "/" not in lowered):
        return "email"
    if "linkedin.com" in lowered:
        return "linkedin"
    if "github.com" in lowered:
        return "github"
    if any(host in lowered for host in ("behance.net", "dribbble.com", "medium.com", "substack.com")):
        return "portfolio"
    if lowered.startswith("http://") or lowered.startswith("https://"):
        return "website"
    return "other"


def normalize_links_payload(links: Any) -> list[dict[str, Any]]:
    if not isinstance(links, list):
        return []

    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for item in links:
        link_type = ""
        url = ""
        is_primary = False

        if isinstance(item, str):
            url = normalize_link_url(item)
            link_type = infer_link_type(url)
        elif isinstance(item, dict):
            url = normalize_link_url(str(item.get("url") or ""))
            link_type = str(item.get("type") or item.get("link_type") or "").strip().lower()
            if not link_type:
                link_type = infer_link_type(url)
            is_primary = bool(item.get("is_primary", False))
        else:
            continue

        if not url:
            continue

        key = (link_type, url.lower())
        if key in seen:
            continue
        seen.add(key)

        normalized.append({
            "type": link_type or "other",
            "url": url,
            "is_primary": is_primary,
        })

    # Ensure at most one primary per link type; if none marked, first of each type becomes primary.
    by_type_seen_primary: set[str] = set()
    for item in normalized:
        if item["is_primary"] and item["type"] in by_type_seen_primary:
            item["is_primary"] = False
        if item["is_primary"]:
            by_type_seen_primary.add(item["type"])

    for item in normalized:
        if item["type"] not in by_type_seen_primary:
            item["is_primary"] = True
            by_type_seen_primary.add(item["type"])

    return normalized


def replace_profile_links(db: Session, profile_id: uuid.UUID, links: list[dict[str, Any]]) -> None:
    db.execute(delete(ProfileLink).where(ProfileLink.profile_id == profile_id))
    for link in links:
        db.add(
            ProfileLink(
                profile_id=profile_id,
                link_type=str(link["type"]),
                url=str(link["url"]),
                is_primary=bool(link.get("is_primary", False)),
            )
        )


def get_profile_links(db: Session, profile_id: uuid.UUID) -> list[ProfileLink]:
    return list(
        db.scalars(
            select(ProfileLink)
            .where(ProfileLink.profile_id == profile_id)
            .order_by(ProfileLink.link_type.asc(), ProfileLink.is_primary.desc(), ProfileLink.created_at.asc())
        ).all()
    )


def get_profile_link_urls(db: Session, profile_id: uuid.UUID) -> list[str]:
    return [link.url for link in get_profile_links(db=db, profile_id=profile_id)]


def normalize_links_for_legacy_column(links: Iterable[dict[str, Any]]) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for item in links:
        url = str(item.get("url") or "").strip()
        key = url.lower()
        if url and key not in seen:
            seen.add(key)
            urls.append(url)
    return urls
