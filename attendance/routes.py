from flask import request, jsonify
from . import attendance_bp
from datetime import datetime
import sqlite3

@attendance_bp.route('/record_check_in', methods=['POST'])
def record_check_in():
    employee_id = request.form['employee_id']
    check_in_time = request.form['check_in_time']

    if not check_in_time:
        return jsonify({'error': 'يرجى إدخال وقت الحضور'})

    try:
        check_in = datetime.strptime(check_in_time, '%H:%M')
        expected_check_in = datetime.strptime('09:00', '%H:%M')
    except ValueError:
        return jsonify({'error': 'تنسيق وقت الحضور غير صحيح'})

    late_hours = max((check_in - expected_check_in).total_seconds() / 3600, 0)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO attendance (employee_id, date, check_in, late_hours) VALUES (?, DATE("now"), ?, ?)',
                       (employee_id, check_in_time, late_hours))
        conn.commit()
        return jsonify({'message': f'تم تسجيل الحضور بنجاح. ساعات التأخير: {late_hours}'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()

@attendance_bp.route('/record_check_out', methods=['POST'])
def record_check_out():
    employee_id = request.form['employee_id']
    check_out_time = request.form['check_out_time']

    if not check_out_time:
        return jsonify({'error': 'يرجى إدخال وقت الانصراف'})
    
    try:
        check_out = datetime.strptime(check_out_time, '%H:%M')
        expected_check_out = datetime.strptime('12:00', '%H:%M')
    except ValueError:
        return jsonify({'error': 'تنسيق وقت الانصراف غير صحيح'})
    
    early_departure_hours = max((expected_check_out - check_out).total_seconds() / 3600, 0)
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('UPDATE attendance SET check_out = ?, early_departure_hours = ? WHERE employee_id = ? AND date = DATE("now")',
                       (check_out_time, early_departure_hours, employee_id))
        conn.commit()
        return jsonify({'message': f'تم تسجيل الانصراف بنجاح. ساعات الخروج المبكر: {early_departure_hours}'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()
