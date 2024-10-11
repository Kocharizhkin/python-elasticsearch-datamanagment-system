from quart import Quart
from quart_cors import cors
import os
import asyncio

# Import custom modules
from db.db import Database

from routes.update import create_update_blueprint
from routes.search import create_search_blueprint
from routes.books import create_books_blueprint


class App:
    def __init__(self):
        """Initialize the Quart app and required services."""
        self.app = Quart(__name__)
        self.app = cors(self.app)

        # Set configurations
        self.app.config["MAX_CONTENT_LENGTH"] = 100 * 1024 * 1024

        # Initialize services
        self.db = Database()
        
    async def init_services(self):
        """Async initialization of services."""
        await self.db.init_driver()  # Initialize the Database asynchronously

        # Register blueprints after the database is ready
        self.app.register_blueprint(create_update_blueprint(self.db), url_prefix='/update')
        self.app.register_blueprint(create_search_blueprint(self.db), url_prefix='/search')
        self.app.register_blueprint(create_books_blueprint(self.db), url_prefix='/books')
    
        

    async def run(self, host="0.0.0.0", port=8000):
        """Run the Quart app asynchronously."""
        await self.app.run_task(host=host, port=port)


# Environment configuration
elasticsearch_url = os.getenv('ELASTICSEARCH_URL')

if __name__ == "__main__":
    # Initialize and run the application
    app = App()

    async def start_app():
        await app.init_services()  # Initialize async services
        await app.run()

    asyncio.run(start_app())