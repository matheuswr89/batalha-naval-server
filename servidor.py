import time

from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room

from functions import createBattleshipGame

# Endereço IP do host e porta em que o Servidor de Socket está sendo executado.
HOST = "0.0.0.0"
PORT = 5000

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecret'
socketio = SocketIO(app, cors_allowed_origins='*')

sala = dict()
disconectedsSockets = []

# faz uma requisição para a api de gerar um board


@socketio.on('chat')
def chat(data):
    emit("receiver-msg", data["data"], room=data["room"])


@socketio.on('exit')
def chat(id):
    delete_room_or_player(id)

# gera um board para o usuário


@socketio.on('generate_board')
def generate_board(data):
    id = data["id"]
    room = data["room"]
    resp = {
        "board": createBattleshipGame(),
        "id": id
    }
    emit("resp_gen_board", resp, room=room)

# Verifica se a sala está cheia


def verify_room():
    for i in sala:
        if sala[i]["size"] == 1:
            return i

# Salva o board do usuario


@socketio.on("board")
def send_board(data):
    if data["id"] != '':
        room = data["room"]
        data_board = get_player(room, data["id"])
        board = data["board"]
        data_board["board"] = board
        emit("send_board", sala[room], room=room)
        time.sleep(1)
        print(sala[room])
        emit("get_board", sala[room], room=room)

# altera um board de acordo com as posiçoes passadas


@socketio.on("alter_board")
def alter_board(data):
    if data["id"] != '':
        room = data["room"]
        x = data["x"]
        y = data["y"]
        current_player = get_player(room, data["id"])
        player = get_adversary(room, data["id"])
        if player["board"][x][y] == '0':
            player["board"][x][y] = 'Q'
            current_player["myturn"] = False
            player["myturn"] = True
            sala[room]["acertou"] = False
            print(room)
        else:
            player["board"][x][y] = 'W'
            player["placar"] = player["placar"]+1
            current_player["myturn"] = True
            player["myturn"] = False
            sala[room]["acertou"] = True
            player["acertos"] = player["acertos"] + 1
            if player["acertos"] == 19:
                player["ganhou"] = True
                current_player["ganhou"] = False
        player["cliques"] = player["cliques"] + 1
        emit("send_board", sala[room], room=room)

# Verifica se um usuario se desconectou de uma sala


@socketio.on("disconnect")
def disconect():
    disconectedsSockets.append(request.sid)
    delete_room_or_player(request.sid)
    remove()

# verifica se tem usuarios desconectados no array se tiver vai remover todos


@socketio.on("connection")
def connection():
    remove()


def joinRoom(room, my_id, num=1):
    join_room(room)
    sala[room]["size"] = num
    emit("id_room", f"Your room: {room}", room=room)
    if (num == 2):
        time.sleep(2)
        emit("room_message", "Sala cheia,"+my_id, room=room)

# Inicia ou adiciona um novo usuario na sala


@socketio.on("join")
def on_join(data):
    room = verify_room()
    time.sleep(1)
    username = data["username"]
    my_id = request.sid
    if room == None:
        room = data["room"]
        sala[room] = {"size": 0}
        sala[room]["jogador1"] = {"name": username, "id": my_id,
                                  "placar": 0, "myturn": True, "cliques": 0, "acertos": 0, "ganhou": -1}
        joinRoom(room, my_id)
    else:
        sala[room]["jogador2"] = {"name": username, "id": my_id,
                                  "placar": 0, "myturn": False, "cliques": 0, "acertos": 0, "ganhou": -1}
        joinRoom(room, my_id, 2)

# Pega os dados do jogador pelo id dele


def get_player(room, id):
    if sala[room]["jogador1"]["id"] == id:
        return sala[room]["jogador1"]
    else:
        return sala[room]["jogador2"]

# Pega o board do adversario


def get_adversary(room, id):
    if sala[room]["jogador1"]["id"] == id:
        return sala[room]["jogador2"]
    else:
        return sala[room]["jogador1"]

# Deleta um jogador ou uma sala


def delete_room_or_player(id):
    try:
        for idx, dictionary in enumerate(sala):
            if sala[dictionary]["jogador1"]["id"] == id or sala[dictionary]["jogador2"]["id"] == id:
                del sala[dictionary]
                emit("disconected", "Sala excluida!", room=dictionary)
    except:
        print("O tamanho mudou!")


def remove():
    if len(disconectedsSockets) > 0:
        for i in disconectedsSockets:
            delete_room_or_player(i)
            disconectedsSockets.remove(i)


if __name__ == '__main__':
    socketio.run(app)
