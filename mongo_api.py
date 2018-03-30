from pymongo import MongoClient
import datetime
import os

# функция апдейтит базу контактом или продуктом
client = MongoClient(os.environ["MONGODB_URL"], username=os.environ["MONGODB_USERNAME"],
                     password=os.environ["MONGODB_PASSWORD"], authSource=os.environ["MONGODB_AUTHSOURCE"])
db = client[os.environ["MONGODB_AUTHSOURCE"]]
bookings_coll = db.bookings
bookings_done_coll = db.bookings_done
log_coll = db.log


def update_booking(chat_id, product=None, contact=None, userstory=None, team_size = None, team_name = None):
    if product is not None:
        bookings_coll.update_one(
            {"chat_id": chat_id},
            {
                "$set": {"product": product}
            }
        )

    if contact is not None:
        bookings_coll.update_one(
            {"chat_id": chat_id},
            {
                "$set": {"contact": contact}
            }
        )


    if team_size is not None:
        bookings_coll.update_one(
            {"chat_id": chat_id},
            {
                "$set": {"team_size": team_size}
            }
        )

    if team_name is not None:
        bookings_coll.update_one(
            {"chat_id": chat_id},
            {
                "$set": {"team_name": team_name}
            }
        )

# функция пишет лог в базу

def update_log(chat_id=None, message=None):
    if chat_id is not None and message is not None:
        print(message)
        username = str(message.chat.first_name) + " " + str(message.chat.last_name)

        log_record = {
            "chat_id": message.chat.id,
            "name": username,
            "time": datetime.datetime.now(),
            "message": message.text
        }
        username = str(message.chat.first_name) + " " + str(message.chat.last_name)

        log_coll.insert_one(log_record)


def register_user(message):
    existing_booking = bookings_coll.find_one({"chat_id": message.chat.id})
    print(existing_booking)

    if existing_booking is None:
        username = str(message.chat.first_name) + " " + str(message.chat.last_name)

        booking = {
            "chat_id": message.chat.id,
            "name": username,
            "product": None,
            "contact": None
        }

        # вставляем в монго запись - раз и навсегда
        bookings_coll.insert_one(booking)


def create_registration(call):
    user_id = call.from_user.id
    event_id = call.data
    username = str(call.from_user.first_name) + " " + str(call.from_user.last_name)

    booking = {
        "chat_id": user_id,
        "name": username,
        "event": event_id,
        "contact": None
    }
    bookings_coll.insert_one(booking)

def get_booking_status(message):
    existing_booking = bookings_coll.find_one({"chat_id": message.chat.id})
    if existing_booking is None:
        status = None
    else:
        status = existing_booking["status"]
    return status

def booking_move_to_done(message):
    existing_booking = bookings_coll.find_one({"chat_id": message.chat.id})
    bookings_done_coll.insert_one(existing_booking)
    bookings_coll.delete_many("chat_id": message.chat.id)