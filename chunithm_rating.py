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
RES_DIR: Path = STATIC / 'chunithm'

FONT_MEIRYO: Path =  STATIC / 'meiryo.ttc'
FONT_SIYUAN: Path = STATIC / 'SourceHanSansSC-Bold.otf'
FONT_TBFONT: Path = STATIC / 'Torus SemiBold.otf'

SCORE_RANKS: List[str] = ['d', 'c', 'b', 'bb', 'bbb', 'a', 'aa', 'aaa', 's', 'splus', 'ss', 'ssplus', 'sss', 'sssplus']
VERSION_NAME = {
    None: '',
    '': '',
    'CHUNITHM': 'CHUNI',
    'CHUNITHM PLUS': 'CHUNI+',
    'AIR': 'AIR',
    'AIR PLUS': 'AIR+',
    'STAR': 'STAR',
    'STAR PLUS': 'STAR+',
    'AMAZON': 'AMAZON',
    'AMAZON PLUS': 'AMAZON+',
    'CRYSTAL': 'CRYS',
    'CRYSTAL PLUS': 'CRYS+',
    'PARADISE': 'PARA',
    'PARADISE LOST': 'PARA+',
    'CHUNITHM NEW': 'NEW',
    'CHUNITHM NEW PLUS': 'NEW+',
    'SUN': 'SUN',
    'SUN PLUS': 'SUN+',
    'LUMINOUS': 'LUM',
    'LUMINOUS PLUS': 'LUM+',
    'VERSE': 'VERSE',
    'VERSE PLUS': 'VERSE+',
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
    difficulty: int
    is_full_combo: bool
    is_all_justice: bool
    is_clear: bool
    judge_miss: int
    judge_attack: int
    judge_justice: int
    judge_critical: int
    rank: int
    music: MusicInfo


class Rating(BaseModel):
    score: int
    rating: float
    playlog: Record

    song_rating: float
    image_name: str
    version: Optional[str]



class UserInfo(BaseModel):
    user_name: str
    character: str
    level: int
    rating: int
    best_rating: float
    best_new_rating: float
    best_rating_list: List[Rating]
    best_new_rating_list: List[Rating]


class Params(BaseModel):
    show_justice: Optional[bool]


class RequestPayload(BaseModel):
    data: UserInfo
    params: Params


with open(RES_DIR / 'data.json', 'r') as f:
    music_data = json.load(f)
    music_list: List = music_data["songs"]


async def getAvatar(avatar) -> Image.Image:
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.get(f'https://oss-hd1.bemanicn.com/chunithm/character/{avatar}.webp') as req:
                return Image.open(BytesIO(await req.read()))
        except:
            return Image.open(RES_DIR / 'cover_fallback.webp')
            

async def getCover(song: Rating) -> Image.Image:
    try:
        return Image.open(RES_DIR / 'cover_ori' / song.image_name).convert('RGBA')
    except Exception as e:
        return Image.open(RES_DIR / 'cover_fallback.webp')


class Draw:
    basic = Image.open(RES_DIR / 'pattern_basic.png')
    advanced = Image.open(RES_DIR / 'pattern_advanced.png')
    expert = Image.open(RES_DIR / 'pattern_expert.png')
    master = Image.open(RES_DIR / 'pattern_master.png')
    ultima = Image.open(RES_DIR / 'pattern_ultima.png')
    _diff = [basic, advanced, expert, master, ultima]

    def __init__(self, image: Image.Image = None, params: Params = Params()) -> None:
        self._im = image
        dr = ImageDraw.Draw(self._im)
        self._mr = DrawText(dr, FONT_MEIRYO)
        self._sy = DrawText(dr, FONT_SIYUAN)
        self._tb = DrawText(dr, FONT_TBFONT)
        self.params = params


    async def whiledraw(self, data: List[Rating], height: int = 0) -> None:
        # y为第一排纵向坐标，dy为各排间距
        dy = 170
        y = height
        TEXT_COLOR = [(255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255), (255, 255, 255, 255)]
        x = 70
        for num, info in enumerate(data):
            if num % 5 == 0:
                x = 70
                y += dy if num != 0 else 0
            else:
                x += 416

            cover = (await getCover(info)).resize((135, 135))

            self._im.alpha_composite(self._diff[info.playlog.difficulty], (x, y))
            self._im.alpha_composite(cover, (x + 5, y + 5))

            self._sy.draw(x + 8, y + 149, 18, f'#{num + 1}', TEXT_COLOR[info.playlog.difficulty], anchor='lm')
            self._sy.draw(x + 136, y + 149, 18, f'{VERSION_NAME[info.version]}', TEXT_COLOR[info.playlog.difficulty], anchor='rm')

            rate = Image.open(RES_DIR / 'score' / f'score_{SCORE_RANKS[info.playlog.rank]}.png').resize((120, 34))
            self._im.alpha_composite(rate, (x + 146, y + 82))
            
            if info.playlog.is_all_justice and info.playlog.judge_justice == 0:
                fc_img = 'score_detail_ajc.png'
            elif info.playlog.is_all_justice:
                fc_img = 'score_detail_aj.png'
            elif info.playlog.is_full_combo:
                fc_img = 'score_detail_fc.png'
            elif info.playlog.is_clear:
                fc_img = 'score_detail_clear.png'
            else:
                fc_img = None
            
            if fc_img:
                fc = Image.open(RES_DIR / 'score' / fc_img).convert('RGBA').resize((120, 34))
                self._im.alpha_composite(fc, (x + 270, y + 82))

            title = info.playlog.music.name
            if coloumWidth(title) > 20:
                title = changeColumnWidth(title, 19) + '...'
            self._sy.draw(x + 152, y + 20, 20, title, TEXT_COLOR[info.playlog.difficulty], anchor='lm')
            self._tb.draw(x + 152, y + 56, 38, f'{info.score}', TEXT_COLOR[info.playlog.difficulty], anchor='lm')
            if self.params.show_justice:
                self._tb.draw(x + 342, y + 132, 22, f'{info.playlog.judge_justice}-{info.playlog.judge_attack}-{info.playlog.judge_miss}', TEXT_COLOR[info.playlog.difficulty], anchor='mm')
            else:
                self._tb.draw(x + 342, y + 132, 22, f'{info.playlog.judge_attack}-{info.playlog.judge_miss}', TEXT_COLOR[info.playlog.difficulty], anchor='mm')
            self._tb.draw(x + 152, y + 132, 22, f'{info.song_rating:.01f} -> {info.rating:.02f}', TEXT_COLOR[info.playlog.difficulty], anchor='lm')


class DrawBest(Draw):
    def __init__(self, data: UserInfo, params: Params) -> None:
        super().__init__(Image.open(RES_DIR / 'bg.png').convert('RGBA').resize((2200, 2500)), params)
        self.data = data

    def _getRatingIndex(self) -> int:
        rating_ranges = [0, 400, 700, 1000, 1200, 1325, 1450, 1450, 1525, 1600, 2000]
        for i, r in enumerate(rating_ranges):
            if self.data.rating < r:
                return i
        else:
            return 10

    async def draw(self) -> Image.Image:
        rating_index = self._getRatingIndex()

        rating_number = Image.open(RES_DIR / 'rating' / f'num_{rating_index}.png')
        rating_numbers = []
        for j in range(4):
            for i in range(4):
                rating_numbers.append(rating_number.crop((34*i, 37*j, 34*(i+1), 37*(j+1))))

        logo = Image.open(RES_DIR / 'logo.png').convert('RGBA').resize((320, 240))
        rating_header = Image.open(RES_DIR / 'rating' / f'header_{rating_index}.png').resize((158, 42))
        level = Image.open(RES_DIR / 'rating' / 'level_bg.png')
        name_bg = Image.open(RES_DIR / 'name_bg.png')
        rating_bg = Image.open(RES_DIR / 'extra_bg.png').resize((454, 50))
        bg_chara = Image.open(RES_DIR / 'bg_chara.png')

        self._im.alpha_composite(logo, (40, 94))
        self._im.alpha_composite(bg_chara, (1000, 2000))

        plate = Image.open(RES_DIR / 'plate.png').resize((1420, 230))
        self._im.alpha_composite(plate, (390, 100))
        icon = Image.open(RES_DIR / 'icon_bg.png').resize((214, 214))
        self._im.alpha_composite(icon, (398, 108))
        try:
            avatar = await getAvatar(self.data.character)
            self._im.alpha_composite(Image.new('RGBA', (203, 203), (255, 255, 255, 255)), (404, 114))
            self._im.alpha_composite(avatar.convert('RGBA').resize((201, 201)), (405, 115))
        except Exception:
            pass

        self._im.alpha_composite(rating_header, (620, 280))
        rating_str = f'{self.data.rating:04d}'
        rating_str = rating_str[0:2] + '.' + rating_str[2:]
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

        self._mr.draw(682, 226, 56, self.data.level, (255, 255, 255, 200), 'lm')
        self._sy.draw(774, 217, 40, self.data.user_name, (0, 0, 0, 255), 'lm')
        self._tb.draw(847, 141, 28, f'B30: {self.data.best_rating:.2f},  B20: {self.data.best_new_rating:.2f}', (0, 0, 0, 255), 'mm', 3, (255, 255, 255, 255))
        # self._mr.draw(1100, 2465, 35, f'Designed by Yuri-YuzuChaN & BlueDeer233 & Hieuzest', (0, 50, 100, 255), 'mm', 3, (255, 255, 255, 255))

        await self.whiledraw(self.data.best_rating_list, 400)
        await self.whiledraw(self.data.best_new_rating_list, 1460)

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
        return fastapi.Response(output_buffer.getvalue(), media_type='image/png')
    
    uvicorn.run(app, host='127.0.0.1', port=5152)
