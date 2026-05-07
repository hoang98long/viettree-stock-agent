"""Persistence repositories."""

from sqlalchemy.orm import Session

from db.models import AnalysisRun


class AnalysisRunRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        symbol: str,
        decision: dict,
        alerts: list,
        metadata: dict,
    ) -> AnalysisRun:
        entity = AnalysisRun(
            symbol=symbol,
            decision=decision,
            alerts=alerts,
            metadata=metadata,
        )
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity
