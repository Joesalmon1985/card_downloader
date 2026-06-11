from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class CardPrinting:
    id: str
    oracle_id: str
    name: str
    lang: str
    layout: str
    set_code: str
    set_name: str
    set_type: str
    collector_number: str
    digital: bool
    games: tuple[str, ...]
    border_color: str
    frame: str
    frame_effects: tuple[str, ...]
    full_art: bool
    promo: bool
    promo_types: tuple[str, ...]
    variation: bool
    finishes: tuple[str, ...]
    highres_image: bool
    image_status: str
    image_uris: dict[str, str]
    card_faces: tuple[dict[str, Any], ...]
    scryfall_uri: str
    released_at: str
    reprint: bool
    raw: dict[str, Any] = field(repr=False, compare=False)

    @classmethod
    def from_api_dict(cls, data: dict[str, Any]) -> "CardPrinting":
        faces = tuple(data.get("card_faces") or ())
        image_uris = dict(data.get("image_uris") or {})
        return cls(
            id=data["id"],
            oracle_id=data.get("oracle_id") or "",
            name=data.get("name") or "",
            lang=data.get("lang") or "en",
            layout=data.get("layout") or "normal",
            set_code=data.get("set") or "",
            set_name=data.get("set_name") or "",
            set_type=data.get("set_type") or "",
            collector_number=str(data.get("collector_number") or ""),
            digital=bool(data.get("digital")),
            games=tuple(data.get("games") or ()),
            border_color=data.get("border_color") or "black",
            frame=data.get("frame") or "2015",
            frame_effects=tuple(data.get("frame_effects") or ()),
            full_art=bool(data.get("full_art")),
            promo=bool(data.get("promo")),
            promo_types=tuple(data.get("promo_types") or ()),
            variation=bool(data.get("variation")),
            finishes=tuple(data.get("finishes") or ()),
            highres_image=bool(data.get("highres_image")),
            image_status=data.get("image_status") or "missing",
            image_uris=image_uris,
            card_faces=faces,
            scryfall_uri=data.get("scryfall_uri") or "",
            released_at=data.get("released_at") or "",
            reprint=bool(data.get("reprint")),
            raw=data,
        )

    def has_playable_image(self) -> bool:
        if self.layout in {"transform", "modal_dfc", "double_faced_token", "split", "flip"}:
            if not self.card_faces:
                return False
            return bool(self.card_faces[0].get("image_uris"))
        return bool(self.image_uris)

    def primary_image_uri(self, size: str = "png") -> str | None:
        if self.card_faces:
            uris = self.card_faces[0].get("image_uris") or {}
            return uris.get(size)
        return self.image_uris.get(size)
