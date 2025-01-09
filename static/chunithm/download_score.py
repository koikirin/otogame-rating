scores = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 'splus', 'ss', 'ssplus', 'sss', 'sssplus']

import requests

for i in range(14):
    score = scores[i]
    url = f'https://u.otogame.net/img/chunithm/icon_rank_{i}.png'
    req = requests.get(url)
    with open(f'score/score_{score}.png', 'wb') as f:
        f.write(req.content)