scores = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 'ss', 'sss', 'sssplus']

import requests

for score in scores:
    url = f'https://u.otogame.net/img/ongeki/score_tr_{score}.png'
    req = requests.get(url)
    with open(f'score_{score}.png', 'wb') as f:
        f.write(req.content)