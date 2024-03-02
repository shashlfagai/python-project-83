from flask import Flask, render_template, request, redirect, url_for, flash
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import requests
import secrets
import psycopg2
from datetime import datetime
import os
import validators

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)
DATABASE_URL = os.getenv('DATABASE_URL')


def connect_to_database():
    return psycopg2.connect(DATABASE_URL)


@app.route('/')
def page_analyzer():
    return render_template('index.html')


@app.route('/urls', methods=['POST', 'GET'])
def analyzed_pages():
    if request.method == 'GET':
        conn = connect_to_database()
        cur = conn.cursor()
        cur.execute("""
            SELECT
            urls.id,
            urls.name,
            MAX(url_checks.created_at) AS max_created_at,
            url_checks.status_code
            FROM
            urls
            LEFT JOIN
            url_checks ON urls.id = url_checks.url_id
            GROUP BY
            urls.id, urls.name,
            url_checks.status_code
            ORDER BY
            urls.id DESC
        """)
        rows = cur.fetchall()
        table_html = ""
        for row in rows:
            id = row[0]
            for column in row:
                if column is not None:
                    if isinstance(column, str) and column.startswith("http"):
                        table_html += "<td>\
                            <a href='/urls/{}'>{}</a>\
                                </td>".format(id, column)
                    else:
                        table_html += "<td>{}</td>".format(column)
                else:
                    table_html += "<td></td>"
            table_html += "</tr>"
        cur.close()
        conn.close()
        return render_template('urls.html', table=table_html)
    else:
        name = request.form.get('url')
        if validators.url(name):
            conn = connect_to_database()
            created_at = datetime.now().date()
            cur = conn.cursor()
            parse_name = urlparse(name)
            name = parse_name.scheme + '://' + parse_name.netloc
            try:
                cur.execute(
                    "SELECT COUNT(*) FROM urls WHERE name = %s",
                    (name,)
                )
                count = cur.fetchone()[0]
                if count == 0:
                    message = 'Страница успешно добавлена'
                    category = 'success'
                    cur.execute(
                        'INSERT INTO urls (name, created_at)\
                            VALUES (%s, %s) RETURNING id',
                        (name, created_at)
                    )
                    url_id = cur.fetchone()[0]
                    conn.commit()
                    cur.close()
                else:
                    message = 'Страница уже существует'
                    category = 'info'
                    cur.execute("SELECT id FROM urls WHERE name = %s", (name,))
                    url_id = cur.fetchone()[0]
                    cur.close()
                conn.close()
                flash(message, category)
                return redirect(
                    url_for('showing_info', id=url_id)
                )
            except psycopg2.Error as e:
                flash('Произошла ошибка при добавлении страницы', 'danger')
                print(e)
                return redirect(url_for('page_analyzer'))
        else:
            flash('Некорректный URL', 'danger')
            return redirect(url_for('page_analyzer'))


@app.route('/urls/<id>', methods=['GET', 'POST'])
def showing_info(id):
    if request.method == 'GET':
        conn = connect_to_database()
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
        conn.close()
        return render_template(
            'url.html',
            id=id,
            url=url,
            date=created_at,
            table_check=table_html
        )
    else:
        redirect(url_for('check_url', id=id))


@app.post('/urls/<id>/checks')
def check_url(id):
    conn = connect_to_database()
    created_at = datetime.now().date()
    cur = conn.cursor()
    cur.execute("SELECT name FROM urls WHERE id = %s", (id,))
    data = cur.fetchall()[0]
    url = data[0]
    try:
        response = requests.get(url)
        status_code = response.status_code
        html_content = response.text
        soup = BeautifulSoup(html_content, 'html.parser')

        title_tag = soup.find('title')
        title = title_tag.text if title_tag else None

        h1_tag = soup.find('h1')
        h1 = h1_tag.text if h1_tag else None

        description = soup.find('meta', attrs={'name': 'description'})
        content = description['content'] if description else None

        cur.execute("""
            INSERT INTO
            url_checks (
                url_id, status_code, h1, title, description, created_at
            )
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (id, status_code, h1, title, content, created_at))
        conn.commit()
        cur.close()
    except (
        requests.exceptions.ConnectionError,
        requests.exceptions.RequestException
    ):
        flash('Произошла ошибка при проверке', 'danger')
    conn.close()
    return redirect(url_for('showing_info', id=id))


if __name__ == '__main__':
    app.run()
