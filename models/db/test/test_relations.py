from sqlalchemy import create_engine, Column, Integer, String, JSON, Text, Date, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# Database configuration
DATABASE_URI = 'postgresql+psycopg2://mkniga:mkniga@localhost:5432/mkniga'

# Create the database engine
engine = create_engine(DATABASE_URI)

# Create a base class for declarative class definitions
Base = declarative_base()

class Books(Base):
    __tablename__ = 'books'
    id = Column(Integer, primary_key=True)
    isbn = Column(String, nullable=True)
    author = Column(String, nullable=True)
    title = Column(String, nullable=True)
    publication_year = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    alpina_id = Column(JSON, nullable=True)
    assorst_id = Column(JSON, nullable=True)
    polyandria_id = Column(JSON, nullable=True)
    azbuka_etc_id = Column(JSON, nullable=True)
    slowbooks_id = Column(JSON, nullable=True)
    omega_id = Column(JSON, nullable=True)
    ast_eksmo_id = Column(JSON, nullable=True)
    individuum_id = Column(JSON, nullable=True)
    mif_id = Column(JSON, nullable=True)
    limbakh_id = Column(JSON, nullable=True)
    supplier_36_6_id = Column(JSON, nullable=True)
    assort_id = Column(JSON, nullable=True)
    ts = Column(Text, nullable=True)

class AstEksmo(Base):
    __tablename__ = 'ast_eksmo'
    id = Column(Integer, primary_key=True)
    update_date = Column(Date, nullable=True)
    publication_year = Column(String, nullable=True)
    page_count = Column(String, nullable=True)
    weight = Column(Float, nullable=True)
    supplier_price = Column(Float, nullable=True)
    display_price = Column(Float, nullable=True)
    delivery_timelines = Column(Text, nullable=True)
    isbn = Column(String, nullable=True)
    dimensions = Column(String, nullable=True)
    author = Column(String, nullable=True)
    book_supplier = Column(String, nullable=True)
    title = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    cover = Column(Text, nullable=True)

class Database:
    def __init__(self, uri):
        self.engine = create_engine(uri)
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()

    def get_unlisted_ast_eksmo_ids(self):
        # Extract the list of ast_eksmo_id from the books table
        books_with_ids = self.session.query(Books.ast_eksmo_id).filter(Books.ast_eksmo_id.isnot(None)).all()
        ids = set()
        for entry in books_with_ids:
            if entry.ast_eksmo_id:
                ids.update(entry.ast_eksmo_id)

        # Query to find IDs in ast_eksmo that are not listed in ast_eksmo_id field in books
        results = self.session.query(AstEksmo.id).filter(AstEksmo.id.not_in(ids)).all()
        return [result.id for result in results]

    def close(self):
        self.session.close()

class AstEksmoService:
    def __init__(self, db):
        self.db = db

    def find_unlisted_ids(self):
        return self.db.get_unlisted_ast_eksmo_ids()

class Tests:
    def test_relations(self):
        db = Database(DATABASE_URI)
        ast_eksmo_service = AstEksmoService(db)

        unlisted_ids = ast_eksmo_service.find_unlisted_ids()
        with open('./update_relations_test.txt', 'w') as f:
            for _id in unlisted_ids:
                f.write(f'{_id}\n')
            f.write('done')

        db.close()