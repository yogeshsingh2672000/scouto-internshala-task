from flask import Flask, request, jsonify, render_template, redirect
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, create_engine
from datetime import date



engine = create_engine('sqlite:///book.db')
app = Flask(__name__)
db = SQLAlchemy(app)



# REST APIs

# page not foudn 404
@app.errorhandler(404)
def page_not_found(e):
    return redirect('/')

## routes for book db
# homepage
@app.route('/', methods = ['GET'])
def welcome():
    with engine.connect() as connection:
        try:
            book_res = []
            books_output = connection.execute(text(f"select * from books"))
            for row in books_output:
                temp = {}
                temp["id"] = row[0]
                temp["name"] = row[1]
                temp["category"] = row[2]
                temp["rent_per_day"] = row[3]
                book_res.append(temp)

            books_transactions_res = []
            books_transactions_output = connection.execute(text(f"select * from transactions"))
            for row in books_transactions_output:
                temp = {}
                temp["transaction_id"] = row[0]
                temp["book_id"] = row[1]
                temp["person_name"] = row[2]
                temp["issue_date"] = row[3]
                temp["return_date"] = row[4]
                temp["rent_collected"] = row[5]
                books_transactions_res.append(temp)
            rent = books_transactions_res[-1]["rent_collected"]
        except:
            return "Please Enter valid parameters"
        if len(book_res) == 0:
            return render_template('index.html')
        else:
            return render_template('index.html', books=book_res, transactions=books_transactions_res, rent=rent)

# Use parameter http://127.0.0.1:5000/getbook?name='book name'
@app.route('/getbook', methods = ['GET'])
def getBook():
    with engine.connect() as connection:
        user = request.args.get('name')
        try:
            output = connection.execute(text(f"select * from books where book_name regexp '^{user.title()}'"))
            res = []
            for row in output:
                temp = {}
                temp["id"] = row[0]
                temp["name"] = row[1]
                temp["category"] = row[2]
                temp["rent_per_day"] = row[3]
                res.append(temp)
        except:
            return "Please Enter valid parameters"
        if len(res) == 0:
            return "No result found"
        else:
            return jsonify(res)


# Use parameter http://127.0.0.1:5000/pricerange?min=10&max=200
@app.route('/pricerange', methods = ['GET'])
def price():
    with engine.connect() as connection:
        min_range = request.args.get('min')
        max_range = request.args.get('max')
        try:
            output = connection.execute(text(f"SELECT * FROM books WHERE rent_per_day >= '{min_range}' AND rent_per_day <= '{max_range}'"))
            res = []
            for row in output:
                temp = {}
                temp["id"] = row[0]
                temp["name"] = row[1]
                temp["category"] = row[2]
                temp["rent_per_day"] = row[3]
                res.append(temp)
        except:
            return "Please Enter valid parameters"
        if len(res) == 0:
            return "No result found"
        else:
            return jsonify(res)

# Use parameter http://127.0.0.1:5000/nameCategoryPrice?name=name&category=category&min=10&max=200
@app.route('/namecategoryprice', methods = ['GET'])
def nameCategoryPrice():
    with engine.connect() as connection:
        name = request.args.get('name')
        category = request.args.get('category')
        min_range = request.args.get('min')
        max_range = request.args.get('max')

        try:
            output = connection.execute(text(f"SELECT * FROM books WHERE category regexp '^{category.title()}' AND (rent_per_day >= '{min_range}' AND rent_per_day <= '{max_range}') AND book_name regexp '^{name.title()}'"))
            res = []
            for row in output:
                temp = {}
                temp["id"] = row[0]
                temp["name"] = row[1]
                temp["category"] = row[2]
                temp["rent_per_day"] = row[3]
                res.append(temp)
        except:
            return "Please Enter valid parameters"
        if len(res) == 0:
            return "No result found"
        else:
            return jsonify(res)



# API Routes for transaction tables

# Issue Book
@app.route('/issuebook', methods = ['POST'])
def issueBook():
    if request.method == 'POST':
        book_id = request.form['book-id-1']
        person_name = request.form['person-name-1']
        issue_date = request.form['issue-date']
        if int(book_id) not in range(1, 21):
            return "This is not a valid book Id"
    with engine.connect() as connection:
        try:
            res = []
            getting_last_id = connection.execute(text(f"SELECT * FROM transactions"))
            for row in getting_last_id:
                res.append(row)
            last_id = res[-1][0]
            connection.execute(text(f"INSERT INTO transactions (transaction_id, book_id, person_name, issue_date, return_date) VALUES ({last_id+1}, {book_id}, '{person_name}', '{issue_date}', NULL)"))
            db.session.commit()
            return redirect("/")
        except:
            return "please fill all the values"

# Return book
@app.route('/returnbook', methods = ['POST'])
def returnBook():
     if request.method == 'POST':
        book_id = request.form['book-id-2']
        person_name = request.form['person-name-2']
        return_date = request.form['return-date']

        if int(book_id) not in range(1, 21):
            return "This is not a valid book Id"
        with engine.connect() as connection:
            try:
                res = []
                query = connection.execute(text(f"SELECT * from transactions WHERE book_id={book_id} AND return_date IS NULL"))
                for row in query:
                    res.append(row)
                
                transaction_id = res[-1][0]
                issue_date = res[-1][-3]
                verify_person = res[-1][2]
                
                if issue_date>return_date:
                    return "return date cannot be less than issue date"
                elif person_name.lower() != verify_person.lower():
                    return "You are not the person who issued this book"

                return_date = return_date.split("-")
                issue_date = issue_date.split("-")
                
                days = date(int(return_date[0]), int(return_date[1]), int(return_date[2]))-date(int(issue_date[0]), int(issue_date[1]), int(issue_date[2]))

                price_query =  connection.execute(text(f"SELECT id, rent_per_day from books"))

                price = 0
                for row in price_query:
                    if row[0] == book_id:
                        price = row[1]
                        break

                rent = int(days.days)*int(price)

                #updating rent Collected
                query = connection.execute(text(f"UPDATE transactions SET rent_collected = {rent}, return_date='{'-'.join(return_date)}' WHERE transaction_id={transaction_id}"))
                db.session.commit()

                return redirect("/")
            except:
                return "Something went wrong"


if __name__ == "__main__":
    app.run(debug=True)