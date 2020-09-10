import requests
import os
from time import sleep

getMessagesURL = "https://api.vk.com/method/messages.getHistory"
getChatURL = "https://api.vk.com/method/messages.getChat"
getGroupUrl = "https://api.vk.com/method/groups.getById"
getUserUrl = "https://api.vk.com/method/users.get"

session = requests.session()

COUNT = 200

basic = {
    "v": "5.132",
    "access_token": "vk_access_token" # лучше брать токен кейт мобайла
}

chatId = input("Введите id чата для анализа сообщений: ")
while not chatId.isnumeric():
    chatId = input("Введите id чата для анализа сообщений: ")

offset = int(input("Введите смещение сообщений (ноль по умолчанию): ") or "0")
total = offset

sortby = int(input("0 - сортировка списка по кол-ву сообщений, 1 - по длине сообщения: ") or "0")

params = {
    "peer_id": 2000000000 + int(chatId),
    "count": f"{COUNT}"
}
params.update(basic)

users = {}

while True:
    params["offset"] = total
    try:
        items = session.get(getMessagesURL, params=params).json()["response"]["items"]
    except KeyError:
        print("sleep...")
        sleep(1)
        print("slept")
        continue
    print(total)
    for i in items:
        try:
            from_id = i["from_id"]
            msgs = users[from_id][0]
            avg = users[from_id][1]
            users[from_id] = (msgs + 1, (((msgs * avg) + len(i["text"])) / (msgs + 1)))
        except KeyError:
            users[i["from_id"]] = (1, len(i["text"]))
    total += len(items)
    if len(items) < COUNT:
        break
    sleep(0.07)


def PrintUsers(usr, basic_params, chat_id):
    def checkResponse(url, p):
        rsp = requests.get(url, params=p)
        isContinue = False
        while not isContinue:
            try:
                rsp = rsp.json()["response"][0]
                isContinue = True
            except KeyError:
                print("KeyError: " + str(rsp.text))
                print(rsp.url)
                sleep(2)
                rsp = requests.get(url, params=p)
        return rsp

    usr = dict(sorted(usr.items(), key=lambda kv: kv[1][sortby], reverse=True))

    titleGetParams = basic_params.copy()
    titleGetParams["chat_id"] = chat_id
    chatInfo = requests.get(getChatURL, params=titleGetParams).json()["response"]
    string = f"Статистика беседы \"{chatInfo['title']}\"\nНа данный момент в нём {chatInfo['members_count']} " \
             f"участников.\n\n\nСтатистика по сообщениям:\nПроанализировано {total - offset} сообщений. " \
             f"Список сортирован по {'длине сообщений' if sortby else 'количеству сообщений'}.\n\n"

    for key, value in usr.items():
        outparams = basic_params.copy()
        if key < 0:
            outparams["group_ids"] = key * -1
            response = checkResponse(getGroupUrl, outparams)
            string += f"[club{response['id']}|{response['name']}] — {value[0]}" \
                      f" сообщений\nСредняя длина сообщения: {value[1]} символов\n\n"
        else:
            outparams["user_ids"] = key
            response = checkResponse(getUserUrl, outparams)
            string += f"[id{response['id']}|{response['first_name']} {response['last_name']}] — {value[0]}" \
                      f" сообщений\nСредняя длина сообщения: {value[1]} символов\n\n"
        sleep(0.1)
    string.rstrip()
    return chatInfo['title'], string


result = PrintUsers(users, basic, chatId)

fileName = result[0] if len(result[0]) <= 20 else (result[0][:20] + "...")
fileName = f"./results/{fileName}.txt"
os.makedirs(os.path.dirname(fileName), exist_ok=True)

with open(fileName, "w", encoding="UTF-8") as f:
    f.write(result[1])
print("okey")
