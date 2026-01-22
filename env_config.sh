# .env file - Environment variables
SECRET_KEY=your-super-secret-key-here-change-this-in-production

# Database Configuration (uncomment the one you're using)

# SQLite (default)
DATABASE_URL=sqlite:///app.db

# MySQL
# DATABASE_URL=mysql+pymysql://username:password@localhost/your_database_name

# PostgreSQL
# DATABASE_URL=postgresql://username:password@localhost/your_database_name

# Server Configuration
FLASK_ENV=development
FLASK_DEBUG=True
PORT=5000