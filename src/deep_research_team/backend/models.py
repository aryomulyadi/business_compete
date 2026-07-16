from typing import Any, Optional


class BrandConcept:
    name: str
    meaning: str
    philosophy: str
    target_market: str
    positioning: str

    def __init__(
        self,
        name: str = "",
        meaning: str = "",
        philosophy: str = "",
        target_market: str = "",
        positioning: str = "",
    ) -> None:
        self.name = name
        self.meaning = meaning
        self.philosophy = philosophy
        self.target_market = target_market
        self.positioning = positioning

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "meaning": self.meaning,
            "philosophy": self.philosophy,
            "target_market": self.target_market,
            "positioning": self.positioning,
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BrandConcept":
        return cls(
            name=d.get("name", ""),
            meaning=d.get("meaning", ""),
            philosophy=d.get("philosophy", ""),
            target_market=d.get("target_market", ""),
            positioning=d.get("positioning", ""),
        )


class HistoryItem:
    id: int
    field: str
    status: str
    created_at: str
    report_path: Optional[str]
    error: Optional[str]

    def __init__(
        self,
        id: int = 0,
        field: str = "",
        status: str = "running",
        created_at: str = "",
        report_path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        self.id = id
        self.field = field
        self.status = status
        self.created_at = created_at
        self.report_path = report_path
        self.error = error

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "field": self.field,
            "status": self.status,
            "created_at": self.created_at,
            "report_path": self.report_path,
            "error": self.error,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "HistoryItem":
        return cls(
            id=row[0],
            field=row[1],
            status=row[2],
            created_at=row[3],
            report_path=row[4],
            error=row[5],
        )


class LogoItem:
    id: int
    history_row_id: int
    brand_name: str
    concept: str
    svg: str
    png_path: str
    style: str
    created_at: str

    def __init__(
        self,
        id: int = 0,
        history_row_id: int = 0,
        brand_name: str = "",
        concept: str = "",
        svg: str = "",
        png_path: str = "",
        style: str = "",
        created_at: str = "",
    ) -> None:
        self.id = id
        self.history_row_id = history_row_id
        self.brand_name = brand_name
        self.concept = concept
        self.svg = svg
        self.png_path = png_path
        self.style = style
        self.created_at = created_at

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "history_row_id": self.history_row_id,
            "brand_name": self.brand_name,
            "concept": self.concept,
            "svg": self.svg,
            "png_path": self.png_path,
            "style": self.style,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: tuple) -> "LogoItem":
        return cls(
            id=row[0],
            history_row_id=row[1],
            brand_name=row[2],
            concept=row[3],
            svg=row[4],
            png_path=row[5],
            style=row[6],
            created_at=row[7],
        )
