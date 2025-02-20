from flask import Flask, render_template, request, jsonify
import sqlite3
from datetime import datetime

app = Flask(__name__)

# قائمة بأسماء الموظفين المسبقة الإنشاء
PREDEFINED_NAMES = ["فتحي", "شوقي", "إسكندر"]

# قائمة بالمناصب المسبقة الإنشاء
PREDEFINED_POSITIONS = [
    "مدير الموارد البشرية",
    "مدير مكتب المدير",
    "مدير إدارة الحسابات"
]

# قائمة بالرواتب المسبقة الإنشاء
PREDEFINED_SALARIES = [f"${amount:,}" for amount in [2000000, 1000000, 700000]]

# إنشاء قاعدة بيانات وجدول الموظفين إذا لم يكن موجودًا
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # إنشاء جدول الموظفين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            position TEXT NOT NULL,
            salary TEXT NOT NULL,
            annual_leave_balance INTEGER DEFAULT 30,
            emergency_leave_balance INTEGER DEFAULT 10
        )
    ''')
    # إنشاء جدول الحضور والغياب
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT,
            check_out TEXT,
            late_hours REAL DEFAULT 0,
            early_departure_hours REAL DEFAULT 0,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    # إنشاء جدول الإجازات
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leaves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type TEXT NOT NULL, -- 'annual' or 'emergency'
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            days INTEGER NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    conn.commit()
    conn.close()

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template(
        'index.html',
        predefined_names=PREDEFINED_NAMES,
        predefined_positions=PREDEFINED_POSITIONS,
        predefined_salaries=PREDEFINED_SALARIES
    )

# إضافة موظف
@app.route('/add_employee', methods=['POST'])
def add_employee():
    name = request.form['name']
    position = request.form['position']
    salary = request.form['salary']

    if not name or not position or not salary:
        return jsonify({'error': 'يرجى ملء جميع الحقول'})

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # التحقق من أن الموظف غير موجود بالفعل
        cursor.execute('SELECT id FROM employees WHERE name = ?', (name,))
        existing_employee = cursor.fetchone()
        if existing_employee:
            return jsonify({'error': 'الموظف موجود بالفعل'})

        # إضافة الموظف الجديد
        cursor.execute('INSERT INTO employees (name, position, salary) VALUES (?, ?, ?)', (name, position, salary))
        conn.commit()
        return jsonify({'message': 'تم إضافة الموظف بنجاح'})
    except sqlite3.IntegrityError as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()

# تسجيل الحضور
@app.route('/record_check_in', methods=['POST'])
def record_check_in():
    employee_id = request.form['employee_id']
    check_in_time = request.form['check_in_time']

    if not check_in_time:
        return jsonify({'error': 'يرجى إدخال وقت الحضور'})

    # تحويل وقت الحضور إلى كائن datetime
    try:
        check_in = datetime.strptime(check_in_time, '%H:%M')
        expected_check_in = datetime.strptime('09:00', '%H:%M')
    except ValueError:
        return jsonify({'error': 'تنسيق وقت الحضور غير صحيح'})

    # حساب التأخير
    late_hours = max((check_in - expected_check_in).total_seconds() / 3600, 0)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # تسجيل الحضور
        cursor.execute('INSERT INTO attendance (employee_id, date, check_in, late_hours) VALUES (?, DATE("now"), ?, ?)',
                       (employee_id, check_in_time, late_hours))
        conn.commit()
        return jsonify({'message': f'تم تسجيل الحضور بنجاح. ساعات التأخير: {late_hours}'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()

# تسجيل الانصراف
@app.route('/record_check_out', methods=['POST'])
def record_check_out():
    employee_id = request.form['employee_id']
    check_out_time = request.form['check_out_time']

    if not check_out_time:
        return jsonify({'error': 'يرجى إدخال وقت الانصراف'})

    # تحويل وقت الانصراف إلى كائن datetime
    try:
        check_out = datetime.strptime(check_out_time, '%H:%M')
        expected_check_out = datetime.strptime('12:00', '%H:%M')
    except ValueError:
        return jsonify({'error': 'تنسيق وقت الانصراف غير صحيح'})

    # حساب الخروج المبكر
    early_departure_hours = max((expected_check_out - check_out).total_seconds() / 3600, 0)

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # تحديث وقت الانصراف
        cursor.execute('UPDATE attendance SET check_out = ?, early_departure_hours = ? WHERE employee_id = ? AND date = DATE("now")',
                       (check_out_time, early_departure_hours, employee_id))
        conn.commit()
        return jsonify({'message': f'تم تسجيل الانصراف بنجاح. ساعات الخروج المبكر: {early_departure_hours}'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()

# تسجيل الإجازات
@app.route('/record_leave', methods=['POST'])
def record_leave():
    employee_id = request.form['employee_id']
    leave_type = request.form['leave_type']  # 'annual' or 'emergency'
    start_date = request.form['start_date']
    end_date = request.form['end_date']

    if not start_date or not end_date:
        return jsonify({'error': 'يرجى ملء جميع الحقول'})

    # حساب عدد أيام الإجازة
    start = datetime.strptime(start_date, '%Y-%m-%d')
    end = datetime.strptime(end_date, '%Y-%m-%d')
    days = (end - start).days + 1  # إضافة يوم واحد لأن النطاق شامل

    if days <= 0:
        return jsonify({'error': 'تاريخ الإجازة غير صحيح'})

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # التحقق من الرصيد السنوي أو الطارئ
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

        # تسجيل الإجازة
        cursor.execute('INSERT INTO leaves (employee_id, leave_type, start_date, end_date, days) VALUES (?, ?, ?, ?, ?)',
                       (employee_id, leave_type, start_date, end_date, days))

        # تحديث الرصيد
        new_balance = leave_balance - days
        cursor.execute(f'UPDATE employees SET {balance_column} = ? WHERE id = ?', (new_balance, employee_id))

        conn.commit()
        return jsonify({'message': f'تم تسجيل الإجازة بنجاح. الرصيد المتبقي: {new_balance} يومًا'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()

# توليد التقرير الشهري
@app.route('/generate_report', methods=['GET'])
def generate_report():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        # الحصول على جميع الموظفين
        cursor.execute('SELECT * FROM employees')
        employees = cursor.fetchall()

        report = []
        for employee in employees:
            employee_id = employee[0]
            name = employee[1]
            annual_leave_balance = employee[4]
            emergency_leave_balance = employee[5]

            # الحصول على سجل الحضور والغياب للموظف
            cursor.execute('SELECT SUM(late_hours), SUM(early_departure_hours) FROM attendance WHERE employee_id = ?', (employee_id,))
            attendance_summary = cursor.fetchone()
            total_late_hours = attendance_summary[0] or 0
            total_early_departure_hours = attendance_summary[1] or 0

            # إضافة التقرير الخاص بالموظف
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

# تشغيل التطبيق
if __name__ == '__main__':
    init_db()
    app.run(debug=True)