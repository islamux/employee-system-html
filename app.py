from flask import Flask, render_template
from db import init_db

def create_app():
    app = Flask(__name__)
    app.config['DEBUG'] = True

    # تهيئة قاعدة البيانات
    init_db()

    # تسجيل Blueprints
    from employees import employees_bp
    app.register_blueprint(employees_bp)
    
    from attendance import attendance_bp
    app.register_blueprint(attendance_bp)
    
    from leaves import leaves_bp
    app.register_blueprint(leaves_bp)
    
    from report import report_bp
    app.register_blueprint(report_bp)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    return app

if __name__ == '__main__':
    create_app().run()
