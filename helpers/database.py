from cs50 import SQL

db = SQL("sqlite:///themeparkify.db")


def execute(sql, *args, **kwargs):
    return db.execute(sql, *args, **kwargs)


def get_user_destination_ids(user_id):
    destination_ids = []

    rows = execute("SELECT * FROM destinations WHERE user_id = ?", user_id)
    for row in rows:
        destination_ids.append(row["destination_id"])

    return destination_ids


def get_user_tracks(user_id):
    return db.execute("SELECT * FROM tracks WHERE user_id = ?", user_id)
