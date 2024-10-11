from quart import Blueprint, jsonify, request
import traceback


def create_books_blueprint(db):
    # Create a blueprint for books
    book_bp = Blueprint('books', __name__)

    @book_bp.route('/get_books')
    async def get_books():
        try:
            # Extracting the 'cardsPerRow' parameter from the request, defaulting to None if not provided
            cards_per_row = request.args.get('cardsPerRow', default=None, type=int)

            # Assuming get_next_entries can optionally take a number of entries to fetch
            # If cards_per_row is None, get_next_entries can default to a standard number
            entries = await db.books.get_next_entries(limit=cards_per_row)

            return jsonify(entries)
        except Exception as e:
            print(e)
            # Handle exceptions, possibly logging them
            return jsonify({'error': str(e)}), 500
        
    @book_bp.route('/get_book_supplier')
    async def get_book_supplier():
        try:
            # Extracting the book ID parameter from the request
            book_id = request.args.get('bookId', default=None, type=int)

            # Validate that book_id is provided
            if book_id is None:
                return jsonify({'error': 'Book ID is required'}), 400

            # Assuming get_supplier_info is a method to fetch supplier details by book ID
            supplier_info = await db.books.get_supplier_info(book_id)

            return jsonify(supplier_info)
        except Exception as e:
            print(e)
            traceback.print_exc()
            # Handle exceptions, possibly logging them
            return jsonify({'error': str(e)}), 500
        
    return book_bp