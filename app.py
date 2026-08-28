import os
from flask import Flask
from config import Config
from database import db
from database.models import Document, Conversation, Message

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    with app.app_context():
        # Ensure database tables and initial seed data exist
        from database.seed import init_db
        init_db(app)

        # Register Blueprints
        from routes.api import api_bp
        from routes.views import views_bp
        app.register_blueprint(api_bp, url_prefix='/api')
        app.register_blueprint(views_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5001))
    print(f"==================================================")
    print(f" RAG Chatbot - PDF Question Answering System")
    print(f" Server running at: http://127.0.0.1:{port}")
    print(f" Demo Mode: {Config.DEMO_MODE}")
    print(f"==================================================")
    app.run(debug=True, port=port, host='0.0.0.0')
