import aiohttp
import asyncio
import base64
import json
import time

from pathlib import Path
from io import BytesIO
from typing import List, Optional, Tuple, Union

from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel


ROOT: Path = Path(__file__).parent
STATIC: Path = ROOT / 'static'
RES_DIR: Path = STATIC / 'ongeki'

FONT_MEIRYO: Path =  STATIC / 'meiryo.ttc'
FONT_SIYUAN: Path = STATIC / 'SourceHanSansSC-Bold.otf'
FONT_TBFONT: Path = STATIC / 'Torus SemiBold.otf'

SCORE_RANKS: List[str] = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 'ss', 'sss', 'sssplus']
VERSION_NAME = {
    'オンゲキ': 'ONGEKI',
    'オンゲキ PLUS': 'ONGEKI+',
    'SUMMER': 'SUMMER',
    'SUMMER PLUS': 'SUMMER+',
    'R.E.D.': 'R.E.D.',
    'R.E.D. PLUS': 'R.E.D.+',
    'bright': 'BRIGHT',
    'bright MEMORY': 'BRIGHT+',
    'Re:Fresh': 'REFRESH',
}


class DrawText:
    def __init__(self, image: ImageDraw.ImageDraw, font: Path) -> None:
        self._img = image
        self._font = str(font)

    def get_box(self, text: str, size: int):
        return ImageFont.truetype(self._font, size).getbbox(text)

    def draw(self,
            pos_x: int,
            pos_y: int,
            size: int,
            text: Union[str, int, float],
            color: Tuple[int, int, int, int] = (255, 255, 255, 255),
            anchor: str = 'lt',
            stroke_width: int = 0,
            stroke_fill: Tuple[int, int, int, int] = (0, 0, 0, 0),
            multiline: bool = False):

        font = ImageFont.truetype(self._font, size)
        if multiline:
            self._img.multiline_text((pos_x, pos_y), str(text), color, font, anchor, stroke_width=stroke_width, stroke_fill=stroke_fill)
        else:
            self._img.text((pos_x, pos_y), str(text), color, font, anchor, stroke_width=stroke_width, stroke_fill=stroke_fill)


class MusicInfo(BaseModel):
    music_id: str
    name: str
    artist: str


class Record(BaseModel):
    is_full_combo: bool
    is_full_bell: bool
    is_all_break: bool
    judge_miss: int
    judge_hit: int
    judge_break: int
    judge_critical_break: int
    tech_score_rank: int


class Rating(BaseModel):
    difficulty: int
    music: MusicInfo
    score: int
    rating: float
    playlog: Record
    song_rating: float


class UserInfo(BaseModel):
    user_name: str
    avatar: str
    level: int
    battle_point: int
    rating: int
    calc_rating: float
    best_rating: float
    best_new_rating: float
    # hot_rating: int
    best_rating_list: List[Rating]
    best_new_rating_list: List[Rating]
    # hot_rating_list: List[Rating]


class Params(BaseModel):
    show_break: Optional[bool]


class RequestPayload(BaseModel):
    data: UserInfo
    params: Params


music_list: List

def loadData():
    global music_list
    with open(RES_DIR / 'data.json', 'r') as f:
        music_data = json.load(f)
        music_list = music_data["songs"]

loadData()

async def getAvatar(avatar) -> Image.Image:
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.get(f'https://oss.bemanicn.com/SDDT/icon/{avatar}.webp-thumbnail') as req:
                return Image.open(BytesIO(await req.read()))
        except:
            return Image.open(RES_DIR / 'cover_fallback.webp')
            

async def getCover(song: MusicInfo) -> Image.Image:
    for s in music_list:
        if s["title"] == song.name and s["artist"] == song.artist:
            try:
                return Image.open(RES_DIR / 'cover_ori' / s["imageName"]).convert('RGBA')
            except Exception as e:
                print('error', song, e)
    else:
        return Image.open(RES_DIR / 'cover_fallback.webp')


def score2diff(score) -> int:
    if score >= 1007500:
        return 200
    elif score >= 1000000:
        return 150 + (score - 1000000) / 150
    else:
        return 100 + (score - 990000) / 200


class Draw:
    basic = Image.open(RES_DIR / 'pattern_basic.png')
    advanced = Image.open(RES_DIR / 'pattern_advanced.png')
    expert = Image.open(RES_DIR / 'pattern_expert.png')
    master = Image.open(RES_DIR / 'pattern_master.png')
    lunatic = Image.open(RES_DIR / 'pattern_lunatic.png')
    _diff = [basic, advanced, expert, master, None, None, None, None, None, None, lunatic]

    def __init__(self, image: Image.Image = None, params: Params = Params()) -> None:
        self._im = image
        dr = ImageDraw.Draw(self._im)
        self._mr = DrawText(dr, FONT_MEIRYO)
        self._sy = DrawText(dr, FONT_SIYUAN)
        self._tb = DrawText(dr, FONT_TBFONT)
        self.params = params


    async def whiledraw(self, data: List[Rating], height: int = 0) -> None:
        # y为第一排纵向坐标，dy为各排间距
        dy = 175
        y = height
        TEXT_COLOR = [(255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), None, None, None, None, None, None, (205, 37, 36, 255)]
        x = 70
        for num, info in enumerate(data):
            if num % 5 == 0:
                x = 70
                y += dy if num != 0 else 0
            else:
                x += 416

            for s in music_list:
                if s["title"] == info.music.name and s["artist"] == info.music.artist:
                    song = s
                    break
            else:
                song = None

            cover = (await getCover(info.music)).resize((135, 135))
            rate = Image.open(RES_DIR / 'score' / f'score_{SCORE_RANKS[info.playlog.tech_score_rank - 1]}.png').resize((95, 44))
            
            self._im.alpha_composite(self._diff[info.difficulty], (x, y))
            self._im.alpha_composite(cover, (x + 5, y + 5))

            self._sy.draw(x + 8, y + 149, 18, f'#{num + 1}', TEXT_COLOR[info.difficulty], anchor='lm')
            self._sy.draw(x + 136, y + 149, 18, f'{VERSION_NAME[song["version"]] if song else "?"}', TEXT_COLOR[info.difficulty], anchor='rm')

            self._im.alpha_composite(rate, (x + 298, y + 36))

            if info.playlog.is_all_break:
                fc_img = 'score_detail_ab.png'
            elif info.playlog.is_full_combo:
                fc_img = 'score_detail_fc.png'
            else:
                fc_img = 'score_detail_fc_base.png'
            fb_img = 'score_detail_fb.png' if info.playlog.is_full_bell else 'score_detail_fb_base.png'
            
            fc = Image.open(RES_DIR / 'score' / fc_img).resize((120, 36))
            self._im.alpha_composite(fc, (x + 146, y + 82))
            fb = Image.open(RES_DIR / 'score' / fb_img).resize((120, 36))
            self._im.alpha_composite(fb, (x + 268, y + 82))

            title = info.music.name
            if coloumWidth(title) > 20:
                title = changeColumnWidth(title, 19) + '...'
            self._sy.draw(x + 152, y + 20, 20, title, TEXT_COLOR[info.difficulty], anchor='lm')
            self._tb.draw(x + 152, y + 56, 38, f'{info.score}', TEXT_COLOR[info.difficulty], anchor='lm')
            if self.params.show_break:
                self._tb.draw(x + 342, y + 132, 22, f'{info.playlog.judge_break}-{info.playlog.judge_hit}-{info.playlog.judge_miss}', TEXT_COLOR[info.difficulty], anchor='mm')
            else:
                self._tb.draw(x + 342, y + 132, 22, f'{info.playlog.judge_hit}-{info.playlog.judge_miss}', TEXT_COLOR[info.difficulty], anchor='mm')
            self._tb.draw(x + 152, y + 132, 22, f'{info.song_rating:.01f} -> {info.rating:.02f}', TEXT_COLOR[info.difficulty], anchor='lm')


class DrawBest(Draw):
    def __init__(self, data: UserInfo, params: Params) -> None:
        super().__init__(Image.open(RES_DIR / 'bg.png').convert('RGBA'), params)
        self.data = data

    def _getRatingIndex(self) -> int:
        rating_ranges = [4000, 7000, 9000, 11000, 13000, 15000, 17000, 18000, 19000, 2000]
        for i, r in enumerate(rating_ranges):
            if self.data.rating < r:
                return i
        else:
            return 10

    def _getRankIndex(self) -> int:
        rank_ranges = [200, 500, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000, 13000, 14000, 15000, 17000, 19000, 20000, 999999]
        rank_bgs = [0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 4, 5, 6, 7]
        for i, r in enumerate(rank_ranges):
            if self.data.battle_point < r:
                return i, rank_bgs[i]
        else:
            return 0, 0

    async def draw(self) -> Image.Image:
        rating_index = self._getRatingIndex()
        rank_index, rank_bg_index = self._getRankIndex()

        rating_number = Image.open(RES_DIR / 'rating' / f'num_{rating_index}.png')
        rating_numbers = []
        for j in range(4):
            for i in range(4):
                rating_numbers.append(rating_number.crop((34*i, 37*j, 34*(i+1), 37*(j+1))))

        logo = Image.open(RES_DIR / 'logo.png').convert('RGBA').resize((380, 210))
        rating_header = Image.open(RES_DIR / 'rating' / f'header_{rating_index}.png').resize((158, 42))
        rank = Image.open(RES_DIR / 'rating' / f'rank_{rank_index}.png')
        rank_bg = Image.open(RES_DIR / 'rating' / f'rank_bg_{rank_bg_index}.png').resize((130, 280))
        level = Image.open(RES_DIR / 'rating' / 'level_bg.png')
        name_bg = Image.open(RES_DIR / 'name_bg.png')
        rating_bg = Image.open(RES_DIR / 'extra_bg.png').resize((454, 50))

        self._im.alpha_composite(logo, (16, 112))

        plate = Image.open(RES_DIR / 'plate.png').resize((1420, 230))
        self._im.alpha_composite(plate, (390, 100))
        icon = Image.open(RES_DIR / 'icon_bg.png').resize((214, 214))
        self._im.alpha_composite(icon, (398, 108))
        try:
            avatar = await getAvatar(self.data.avatar)
            self._im.alpha_composite(Image.new('RGBA', (203, 203), (255, 255, 255, 255)), (404, 114))
            self._im.alpha_composite(avatar.convert('RGBA').resize((201, 201)), (405, 115))
        except Exception:
            pass

        self._im.alpha_composite(rating_header, (620, 280))
        rating_str = f'{self.data.rating:05d}'
        rating_str = rating_str[0:2] + '.' + rating_str[2:]
        print(rating_str)
        for n, i in enumerate(rating_str):
            if n == 0 and i == '0': continue
            if n < 2:
                self._im.alpha_composite(rating_numbers[int(i)].resize((68, 74)), (760 + 50 * n, 252))
            elif n == 2:
                self._im.alpha_composite(rating_numbers[12].resize((45, 49)), (858, 271))
            else:
                self._im.alpha_composite(rating_numbers[int(i)].resize((45, 49)), (790 + 30 * n, 271))

        self._im.alpha_composite(name_bg, (750, 185))
        self._im.alpha_composite(level, (620, 180))
        self._im.alpha_composite(rating_bg, (620, 120))
        self._im.alpha_composite(rank_bg, (1800, 80))
        self._im.alpha_composite(rank, (1826, 195))

        self._mr.draw(682, 226, 56, self.data.level, (255, 255, 255, 200), 'lm')
        self._sy.draw(774, 217, 40, self.data.user_name, (0, 0, 0, 255), 'lm')
        self._tb.draw(847, 141, 28, f'{self.data.best_rating:.3f} | {self.data.best_new_rating:.3f} | {self.data.calc_rating:.3f}', (0, 0, 0, 255), 'mm', 3, (255, 255, 255, 255))
        # self._mr.draw(1100, 2465, 35, f'Designed by Yuri-YuzuChaN & BlueDeer233 & Hieuzest', (0, 50, 100, 255), 'mm', 3, (255, 255, 255, 255))

        await self.whiledraw(self.data.best_rating_list, 380)
        await self.whiledraw(self.data.best_new_rating_list, 2210)
        # await self.whiledraw(self.data.hot_rating_list, 1980)

        return self._im.resize((1760, 2000)).convert('RGB')


def getCharWidth(o) -> int:
    widths = [
        (126, 1), (159, 0), (687, 1), (710, 0), (711, 1), (727, 0), (733, 1), (879, 0), (1154, 1), (1161, 0),
        (4347, 1), (4447, 2), (7467, 1), (7521, 0), (8369, 1), (8426, 0), (9000, 1), (9002, 2), (11021, 1),
        (12350, 2), (12351, 1), (12438, 2), (12442, 0), (19893, 2), (19967, 1), (55203, 2), (63743, 1),
        (64106, 2), (65039, 1), (65059, 0), (65131, 2), (65279, 1), (65376, 2), (65500, 1), (65510, 2),
        (120831, 1), (262141, 2), (1114109, 1),
    ]
    if o == 0xe or o == 0xf:
        return 0
    for num, wid in widths:
        if o <= num:
            return wid
    return 1


def coloumWidth(s: str) -> int:
    res = 0
    for ch in s:
        res += getCharWidth(ord(ch))
    return res


def changeColumnWidth(s: str, len: int) -> str:
    res = 0
    sList = []
    for ch in s:
        res += getCharWidth(ord(ch))
        if res <= len:
            sList.append(ch)
    return ''.join(sList)


def generate(data: UserInfo, params={}):
    loop = asyncio.new_event_loop()
    start = time.time()
    draw = DrawBest(data, params)
    img = loop.run_until_complete(draw.draw())
    print('generated image for', data.user_name, ' cost ', time.time() - start, ' s')
    return img


if __name__ == '__main__':
    import fastapi
    import uvicorn
    
    app = fastapi.FastAPI()

    @app.post('/generate')
    async def _generate(data: RequestPayload):
        img = await asyncio.to_thread(generate, data.data, data.params)
        output_buffer = BytesIO()
        img.save(output_buffer, 'JPEG', optimize=True)
        return fastapi.Response(output_buffer.getvalue(), media_type='image/jpeg')
    
    uvicorn.run(app, host='127.0.0.1', port=5151)
