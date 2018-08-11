import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

with open("books.csv") as f:
    reader = csv.reader(f, delimiter=',')
    lc = 0
    for row in reader:
        if lc != 0:
            # values, so insert into table
            db.execute('INSERT INTO books ("isbn", "title", "author", "year") VALUES (:1,:2,:3,:4)',  {
                "1": row[0],
                "2": row[1],
                "3": row[2],
                "4": int(row[3])
            })

        lc += 1

    db.commit()
