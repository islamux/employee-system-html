from flask import request, jsonify
from . import leaves_bp
from datetime import datetime
import sqlite3

@leaves_bp.route('/record_leave', methods=['POST'])
def record_leave():
    employee_id = request.form['employee_id']
    leave_type = request.form['leave_type']  # annual أو emergency
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    if not start_date or not end_date:
        return jsonify({'error': 'يرجى ملء جميع الحقول'})
    
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'تنسيق التواريخ غير صحيح'})
    
    days = (end - start).days + 1
    if days <= 0:
        return jsonify({'error': 'تاريخ الإجازة غير صحيح'})
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        if leave_type == 'annual':
            cursor.execute('SELECT annual_leave_balance FROM employees WHERE id = ?', (employee_id,))
            balance_column = 'annual_leave_balance'
        elif leave_type == 'emergency':
            cursor.execute('SELECT emergency_leave_balance FROM employees WHERE id = ?', (employee_id,))
            balance_column = 'emergency_leave_balance'
        else:
            return jsonify({'error': 'نوع الإجازة غير صحيح'})
        
        employee = cursor.fetchone()
        if not employee:
            return jsonify({'error': 'الموظف غير موجود'})
        leave_balance = employee[0]
        if leave_balance < days:
            return jsonify({'error': 'رصيد الإجازات غير كافٍ'})
        
        cursor.execute('INSERT INTO leaves (employee_id, leave_type, start_date, end_date, days) VALUES (?, ?, ?, ?, ?)',
                       (employee_id, leave_type, start_date, end_date, days))
        new_balance = leave_balance - days
        cursor.execute(f'UPDATE employees SET {balance_column} = ? WHERE id = ?', (new_balance, employee_id))
        conn.commit()
        return jsonify({'message': f'تم تسجيل الإجازة بنجاح. الرصيد المتبقي: {new_balance} يومًا'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()
