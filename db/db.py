import os

from db.storage.books import BooksStorage
from db.search import Search
from db.helpers.column_mapping import Mapping
from db.db_update import DatabaseUpdater
from db.driver import Driver

class Database:
    def __init__(self):
        self.books = BooksStorage()
        self.update = DatabaseUpdater()
        self.search = Search()
        self.mapping = Mapping()

    async def init_driver(self):
        """Async initialization for the Database."""
        db_url_sync = os.getenv('SYNC_DATABASE_URL')
        db_url_async = os.getenv('ASYNC_DATABASE_URL')
        self.driver = await Driver.create(db_url_sync, db_url_async)
        self.books.driver = self.driver
        self.update.driver = self.driver
        self.search.driver = self.driver
        self.mapping.driver = self.driver