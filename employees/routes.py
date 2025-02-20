from flask import request, jsonify
from . import employees_bp
import sqlite3

@employees_bp.route('/add_employee', methods=['POST'])
def add_employee():
    name = request.form['name']
    position = request.form['position']
    salary = request.form['salary']

    if not name or not position or not salary:
        return jsonify({'error': 'يرجى ملء جميع الحقول'})
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # التحقق من وجود الموظف
        cursor.execute('SELECT id FROM employees WHERE name = ?', (name,))
        if cursor.fetchone():
            return jsonify({'error': 'الموظف موجود بالفعل'})
        cursor.execute('INSERT INTO employees (name, position, salary) VALUES (?, ?, ?)', (name, position, salary))
        conn.commit()
        return jsonify({'message': 'تم إضافة الموظف بنجاح'})
    except sqlite3.IntegrityError as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()
