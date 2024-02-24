from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for
import secrets
import psycopg2
from datetime import datetime
import os
import validators
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
    # conn = psycopg2.connect(DATABASE_URL)
    if request.method == 'GET':
        cur = conn.cursor()
        cur.execute("""
    SELECT urls.id, urls.name, url_checks.created_at, url_checks.status_code
    FROM urls
    LEFT JOIN url_checks ON urls.id = url_checks.url_id
    ORDER BY urls.id DESC
""")
        rows = cur.fetchall()
        table_html = ""
        for row in rows:
            for column in row:
                if column is not None:
                    table_html += "<td>{}</td>".format(column)
                else:
                    table_html += "<td></td>"
            table_html += "</tr>"
        cur.close()
        return render_template('urls.html', table=table_html)
    else:
        # conn = psycopg2.connect(DATABASE_URL)
        name = request.form.get('url')
        created_at = datetime.now().date()
        cur = conn.cursor()
        if validators.url(name):
            try:
                cur.execute(
                    "SELECT COUNT(*) FROM urls WHERE name = %s",
                    (name,)
                )
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
                return redirect(
                    url_for('showing_info', id=url_id)
                )
            except psycopg2.Error as e:
                print(e)
# flash('Ошибка при выполнении запроса к базе данных', 'danger')
                return redirect(url_for('page_analyzer'))
        else:
            return redirect(url_for('page_analyzer'))


@app.route('/urls/<id>', methods=['GET', 'POST'])
def showing_info(id):
    if request.method == 'GET':
        # conn = psycopg2.connect(DATABASE_URL)
        cur = conn.cursor()
        cur.execute("SELECT * FROM urls WHERE id = %s", (id,))
        data = cur.fetchall()[0]
        id = data[0]
        url = data[1]
        created_at = data[2]
        cur.execute("""
        SELECT id, status_code, h1, title, description, created_at
        FROM url_checks
        WHERE url_id = %s
        ORDER BY created_at DESC
        """, (id,))
        rows = cur.fetchall()
        table_html = ""
        for row in rows:
            for column in row:
                if column is not None:
                    table_html += "<td>{}</td>".format(column)
                else:
                    table_html += "<td></td>"
            table_html += "</tr>"
        cur.close()
        return render_template(
            'url.html', id=id, url=url, date=created_at, table_check=table_html
        )
    else:
        redirect(url_for('check_url', id=id))


@app.post('/urls/<id>/checks')
def check_url(id):
    created_at = datetime.now().date()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO
        url_checks (url_id, created_at)
        VALUES (%s, %s)
    """, (id, created_at))
    conn.commit()
    cur.close()
    return redirect(url_for('showing_info', id=id))


if __name__ == '__main__':
    app.run()
