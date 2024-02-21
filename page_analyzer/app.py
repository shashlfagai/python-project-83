from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import secrets
import psycopg2
from datetime import datetime
import os
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
conn = psycopg2.connect(DATABASE_URL)

app = Flask(__name__)
secret_key = secrets.token_hex(32)
app.secret_key = secret_key


@app.route('/')
def page_analyzer():
    return render_template('index.html')


@app.route('/urls', methods=['POST', 'GET'])
def analyzed_pages():
    if request.method == 'GET':
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM urls ORDER BY id DESC")
        rows = cur.fetchall()
        table_html = ""
        for row in rows:
            table_html += "<tr>"
            for column in row:
                table_html += "<td>{}</td>".format(column)
            table_html += "</tr>"
        cur.close()
        return render_template('urls.html', table=table_html)
    else:
        name = request.form.get('url')
        created_at = datetime.now().date()
        cur = conn.cursor()
        try:
            cur.execute("SELECT COUNT(*) FROM urls WHERE name = %s", (name,))
            count = cur.fetchone()[0]
            if count == 0:
                cur.execute(
                    'INSERT INTO urls (name, created_at)\
                        VALUES (%s, %s) RETURNING id',
                    (name, created_at)
                )
                url_id = cur.fetchone()[0]
                conn.commit()
                cur.close()
                # flash('Страница успешно добавлена', 'success')
            else:
                cur.execute("SELECT id FROM urls WHERE name = %s", (name,))
                url_id = cur.fetchone()[0]
                cur.close()
            return redirect(url_for('showing_info', id=url_id))
        except psycopg2.Error:
            # flash('Ошибка при выполнении запроса к базе данных', 'danger')
            return redirect(url_for('page_analyzer'))


@app.route('/urls/<id>')
def showing_info(id):
    cur = conn.cursor()
    cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
    data = cur.fetchall()[0]
    id = data[0]
    url = data[1]
    created_at = data[2]
    cur.close()
    return render_template('url.html', id=id, url=url, date=created_at)


if __name__ == '__main__':
    app.run()
