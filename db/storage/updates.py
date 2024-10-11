import sqlalchemy as sa

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from db.driver import Driver
from db.models import Update


class UpdatesStorage():
    
    async def create(self, session: AsyncSession, total_rows: int) -> Update:
        """
        Creates a new update record and commits it to the database.
        """
        update = Update(current_sheet='', processed_rows=0, total_rows=total_rows)
        session.add(update)
        await session.commit()
        return update

    async def get_progress(self, session: AsyncSession) -> dict:
        """
        Retrieves the latest update record from the database.
        """
        progress = (await session.execute(
            sa.select(Update).order_by(Update.id.desc()).limit(1)
        )).scalar()
        
        if progress:
            return {
                'current_sheet': progress.current_sheet,
                'processed_rows': progress.processed_rows,
                'total_rows': progress.total_rows,
                'update_start_time': progress.update_start_time,
                'time_total': str(progress.time_total)
            }
        else:
            return {}

    async def update(self, session: AsyncSession, update_obj: Update, new_data: dict) -> None:
        """
        Updates the existing update object with new data and commits the changes.
        """
        for key, value in new_data.items():
            if hasattr(update_obj, key):
                setattr(update_obj, key, value)

        try:
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            print(e)
