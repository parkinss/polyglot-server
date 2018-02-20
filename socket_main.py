from flask import Flask, request, redirect
from flask import jsonify
from flask_socketio import SocketIO, emit, send, join_room, leave_room
import time
app = Flask(__name__)
app.config['SECRET KEY'] = 'secret!'
socketio = SocketIO(app)

USER_NAMES = ["Jimmy", "David", "Bob", "Mark", "Alicia", "Tony", "Sam"] #constant storing all available names
Rooms = {"food":[], "sports":[], "movies":[], "hiking":[]} #values are lists of Room objects
Num_rooms = {x:0 for x in Rooms.keys()}



class Room:
    def __init__(self, cat: str, id: int):
        self.room_id = id
        self.number_users = 0
        self.available_names = list(USER_NAMES) #shallow copy of list
        self.active_users = []
        self.category = cat
        self.message_board = [] #list of Message objects

    def add_user(self) -> "User":
        user = User(self.get_available_name(), self.category, self)
        self.active_users.append(user)
        self.number_users += 1
        return user

    def del_user(self, u: "User"):
        self.available_names.insert(0, u.name)
        self.active_users.remove(u)
        self.number_users -= 1

    def get_number_users(self):
        return self.number_users

    def get_available_name(self):
        return self.available_names.pop()

    def get_active_users(self) -> "Users":
       return self.active_users

    def get_active_users_str(self) -> str:
        return [x.name for x in self.active_users]

    def get_messages(self) -> [str]: #returns list of messages, text only
        to_return = []
        for m in self.message_board:
            to_return.append((m.get_text(), m.user, m.time))
        return to_return


class User:
    def __init__(self, n: str, cat: str, room: "Room"):
        self.name = n
        self.cat = cat
        self.room = room

    def add_message(self, text: str):
        self.room.message_board.append(Message(text, self.name))

    def get_name(self):
        return self.name

    def get_cat(self):
        return self.cat


class Message:
    def __init__(self, text: str, user: "User"):
        self.text = text
        self.time = time.asctime(time.localtime(time.time()))
        self.user = user

    def get_text(self):
        return self.text

    def get_time(self):
        return self.time

    def get_user(self):
        return self.user

def init_rooms():
    for key in Rooms.keys():
        Rooms[key].append(Room(key, 0))

@app.route("/rooms/<string:category>/<int:id>", methods= ['POST', 'GET'])
def build_chat(category: str, id: int):
    room = Rooms[category][id]
    if request.method == 'POST':
        get_json = request.get_json(force= True)
        action = get_json['action']
        if action  == "join":
            return jsonify({"username":room.add_user().get_name()})
        elif action == "add_message":
            user = get_json['user']
            text = get_json['text']
            for u in room.get_active_users():
                if user == u.name:
                    u.add_message(text)
                    break

    to_return = {"num_users":room.get_number_users(), "active_users":room.get_active_users_str(),
                 "messages":room.get_messages()}

    return jsonify(to_return)

@app.route("/rooms/<string:category>/<int:id>/messages", methods= ['POST', 'GET'])
def build_messages(category: str, id: int):
    room = Rooms[category][id]

    if request.method == 'POST':
        get_json = request.get_json(force=True)
        add = get_json['add']
        user = add['user']
        for u in room.get_active_users():
            if user == u.name:
                u.add_message(add['text'])

    return jsonify({"messages": room.message_board})

@socketio.on('join')
def on_join(data):
    username = data['name']
    category = data['category']
    id = data['id']
    send(username + 'has entered the room')

@socketio.on('json')
def handleMessage(data):
    emit('message', data['message'], room = data['room'])

@socketio.on('leave')
def on_leave(data):
    print('Client disconnected')

if __name__ == "__main__":
    init_rooms()
    socketio.run(app)