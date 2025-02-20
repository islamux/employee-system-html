from flask import jsonify
from . import report_bp
import sqlite3

@report_bp.route('/generate_report', methods=['GET'])
def generate_report():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()
        report = []
        for employee in employees:
            employee_id = employee[0]
            name = employee[1]
            annual_leave_balance = employee[4]
            emergency_leave_balance = employee[5]
            cursor.execute('SELECT SUM(late_hours), SUM(early_departure_hours) FROM attendance WHERE employee_id = ?', (employee_id,))
            attendance_summary = cursor.fetchone()
            total_late_hours = attendance_summary[0] if attendance_summary[0] is not None else 0
            total_early_departure_hours = attendance_summary[1] if attendance_summary[1] is not None else 0
            report.append({
                'name': name,
                'total_late_hours': total_late_hours,
                'total_early_departure_hours': total_early_departure_hours,
                'annual_leave_balance': annual_leave_balance,
                'emergency_leave_balance': emergency_leave_balance
            })
        return jsonify(report)
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()
