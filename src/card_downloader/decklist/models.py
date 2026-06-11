from dataclasses import dataclass


@dataclass(frozen=True)
class DeckEntry:
    quantity: int
    name: str


@dataclass(frozen=True)
class ParsedDeck:
    entries: tuple[DeckEntry, ...]

    @property
    def total_quantity(self) -> int:
        return sum(e.quantity for e in self.entries)

    @property
    def unique_names(self) -> tuple[str, ...]:
        seen: list[str] = []
        for entry in self.entries:
            if entry.name not in seen:
                seen.append(entry.name)
        return tuple(seen)
