from flask import Flask, render_template, request, jsonify
import sqlite3

app = Flask(__name__)

# إنشاء قاعدة بيانات وجدول الموظفين إذا لم يكن موجودًا
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,  -- إضافة UNIQUE لمنع تكرار الأسماء
            position TEXT NOT NULL,
            salary REAL NOT NULL,
            annual_leave_balance INTEGER DEFAULT 30
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date TEXT NOT NULL,
            status TEXT NOT NULL,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        )
    ''')
    conn.commit()
    conn.close()

# الصفحة الرئيسية
@app.route('/')
def index():
    return render_template('index.html')

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
    except sqlite3.IntegrityError:
        return jsonify({'error': 'حدث خطأ أثناء إضافة الموظف'})
    finally:
        conn.close()

# تعديل بيانات الموظف
@app.route('/update_employee', methods=['POST'])
def update_employee():
    employee_id = request.form['employee_id']
    name = request.form['name']
    position = request.form['position']
    salary = request.form['salary']

    if not name or not position or not salary:
        return jsonify({'error': 'يرجى ملء جميع الحقول'})

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
            UPDATE employees
            SET name = ?, position = ?, salary = ?
            WHERE id = ?
        ''', (name, position, salary, employee_id))
        conn.commit()
        return jsonify({'message': 'تم تحديث بيانات الموظف بنجاح'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()

# حذف موظف
@app.route('/delete_employee', methods=['POST'])
def delete_employee():
    employee_id = request.form['employee_id']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    try:
        cursor.execute('DELETE FROM employees WHERE id = ?', (employee_id,))
        conn.commit()
        return jsonify({'message': 'تم حذف الموظف بنجاح'})
    except Exception as e:
        return jsonify({'error': f'حدث خطأ: {str(e)}'})
    finally:
        conn.close()

# تسجيل الحضور والغياب
@app.route('/record_attendance', methods=['POST'])
def record_attendance():
    employee_id = request.form['employee_id']
    date = request.form['date']
    status = request.form['status']

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT INTO attendance (employee_id, date, status) VALUES (?, ?, ?)', (employee_id, date, status))
    conn.commit()
    conn.close()

    return jsonify({'message': 'تم تسجيل الحدث بنجاح'})

# الحصول على قائمة الموظفين
@app.route('/get_employees', methods=['GET'])
def get_employees():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM employees')
    employees = cursor.fetchall()
    conn.close()

    return jsonify(employees)

# توليد التقرير الشهري
@app.route('/generate_report', methods=['GET'])
def generate_report():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # الحصول على جميع الموظفين
    cursor.execute('SELECT * FROM employees')
    employees = cursor.fetchall()

    report = []
    for employee in employees:
        employee_id = employee[0]
        name = employee[1]
        annual_leave_balance = employee[4]

        # الحصول على سجل الحضور والغياب للموظف
        cursor.execute('SELECT status FROM attendance WHERE employee_id = ?', (employee_id,))
        attendance_records = cursor.fetchall()

        # حساب الغيابات الناتجة عن التأخير والخروج دون إذن
        late_count = sum(1 for record in attendance_records if record[0] == 'late')
        early_leave_count = sum(1 for record in attendance_records if record[0] == 'early-leave')
        absences = (late_count // 2) + (early_leave_count // 2)

        # تحديث رصيد الإجازات السنوية
        annual_leave_balance -= absences

        # إضافة التقرير الخاص بالموظف
        report.append({
            'name': name,
            'absences': absences,
            'annual_leave_balance': max(annual_leave_balance, 0)  # لا يمكن أن يكون الرصيد أقل من صفر
        })

    conn.close()

    return jsonify(report)

# تشغيل التطبيق
if __name__ == '__main__':
    init_db()
    app.run(debug=True)