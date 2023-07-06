import io
import os
from io import BytesIO
import urllib3
from PIL import Image, ImageDraw, ImageFont
from nonebot import logger

from .image_db import imageDB
from ._class import ImageInfo, WeaponData
from .utils import *
from .translation import get_trans_game_mode, get_trans_stage, get_trans_cht_data, dict_weekday_trans

# 根路径
cur_path = os.path.dirname(__file__)

# 图片文件夹
image_folder = os.path.join(cur_path, "staticData", "ImageData")
# 武器文件夹
weapon_folder = os.path.join(cur_path, "staticData", "weapon")
# 字体
ttf_path = os.path.join(cur_path, "staticData", "SplatoonFontFix.otf")
ttf_path_chinese = os.path.join(cur_path, "staticData", "Text.ttf")

http = urllib3.PoolManager()


# 图片转base64
def image_to_base64(image):
    buffered = BytesIO()
    image.save(buffered, format="PNG")
    return buffered.getvalue()


# 取文件
def get_file(name, format_name="png"):
    img = Image.open(os.path.join(image_folder, "{}.{}".format(name, format_name)))
    return img


# 获取武器
def get_weapon(name):
    return Image.open(os.path.join(weapon_folder, "{}".format(name)))


# cf 网站读文件
def get_cf_file_url(url):
    r = cf_http_get(url)
    return r.content


# 普通网页读文件
def get_file_url(url):
    r = http.request("GET", url, timeout=5)
    return r.data


# 向数据库新增或读取素材图片二进制文件
def get_save_file(img: ImageInfo):
    res = imageDB.get_img_data(img.name)
    if not res:
        image_data = get_cf_file_url(img.url)
        if len(image_data) != 0:
            logger.info("[ImageDB] new image {}".format(img.name))
            imageDB.add_or_modify_IMAGE_DATA(img.name, image_data, img.zh_name, img.source_type)
        return Image.open(io.BytesIO(image_data))
    else:
        return Image.open(io.BytesIO(res.get("image_data")))


# 取文件路径
def get_file_path(name, format_name="png"):
    return os.path.join(image_folder, "{}.{}".format(name, format_name))


# 圆角处理
def circle_corner(img, radii):
    """
    圆角处理
    :param img: 源图象。
    :param radii: 半径，如：30。
    :return: 返回一个圆角处理后的图象。
    """
    # 画圆（用于分离4个角）
    circle = Image.new("L", (radii * 2, radii * 2), 0)  # 创建一个黑色背景的画布
    draw = ImageDraw.Draw(circle)
    draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 画白色圆形

    # 原图
    img = img.convert("RGBA")
    w, h = img.size

    # 画4个角（将整圆分离为4个部分）
    alpha = Image.new("L", img.size, 255)
    alpha.paste(circle.crop((0, 0, radii, radii)), (0, 0))  # 左上角
    alpha.paste(circle.crop((radii, 0, radii * 2, radii)), (w - radii, 0))  # 右上角
    alpha.paste(circle.crop((radii, radii, radii * 2, radii * 2)), (w - radii, h - radii))  # 右下角
    alpha.paste(circle.crop((0, radii, radii, radii * 2)), (0, h - radii))  # 左下角

    img.putalpha(alpha)  # 白色区域透明可见，黑色区域不可见
    return alpha, img


# 图片 平铺填充
def tiled_fill(big_image, small_image):
    big_image_w, big_image_h = big_image.size
    small_image_w, small_image_h = small_image.size
    for left in range(0, big_image_w, small_image_w):  # 横纵两个方向上用两个for循环实现平铺效果
        for top in range(0, big_image_h, small_image_h):
            paste_with_a(big_image, small_image, (left, top))
    return big_image


# 图像粘贴 加上a通道参数 使圆角透明
def paste_with_a(image_background, image_pasted, pos):
    _, _, _, a = image_pasted.convert("RGBA").split()
    image_background.paste(image_pasted, pos, mask=a)


# 绘制 地图名称及文字底图
def get_stage_name_bg(stage_name, font_size=25):
    stage_name_bg_size = (len(stage_name * font_size) + 16, 30)
    # 新建画布
    stage_name_bg = Image.new("RGBA", stage_name_bg_size, (0, 0, 0))
    # 圆角化
    _, stage_name_bg = circle_corner(stage_name_bg, radii=16)
    # # 绘制文字
    drawer = ImageDraw.Draw(stage_name_bg)
    ttf = ImageFont.truetype(ttf_path_chinese, font_size)
    # 文字居中绘制
    w, h = ttf.getsize(stage_name)
    text_pos = ((stage_name_bg_size[0] - w) // 2, (stage_name_bg_size[1] - h) // 2)
    drawer.text(text_pos, stage_name, font=ttf, fill=(255, 255, 255))
    return stage_name_bg


# 绘制 时间表头
def get_time_head_bg(time_head_bg_size, date_time, start_time, end_time):
    # 绘制背景
    time_head_bg = get_file("时间表头").resize(time_head_bg_size)
    # 绘制开始，结束时间 文字居中绘制
    ttf = ImageFont.truetype(ttf_path, 40)
    time_head_text = "{}  {} - {}".format(date_time, start_time, end_time)
    w, h = ttf.getsize(time_head_text)
    time_head_text_pos = (
        (time_head_bg_size[0] - w) // 2,
        (time_head_bg_size[1] - h) // 2 - 12,
    )
    drawer = ImageDraw.Draw(time_head_bg)
    drawer.text(time_head_text_pos, time_head_text, font=ttf, fill=(255, 255))
    return time_head_bg


# 是否存在祭典   祭典的结构需要遍历判断
def have_festival(_festivals):
    for v in _festivals:
        if v["festMatchSetting"] is not None:
            return True
    return False


# 绘制 一排 地图卡片
def get_stage_card(
    stage1,
    stage2,
    contest_mode,
    contest_name,
    game_mode,
    start_time="",
    end_time="",
    desc="",
    img_size=(1024, 340),
):
    _, image_background = circle_corner(get_file("背景").resize(img_size), radii=20)

    # 绘制两张地图
    # 计算尺寸，加载图片
    stage_size = (int(img_size[0] * 0.48), int(img_size[1] * 0.7))
    image_left = get_save_file(stage1).resize(stage_size, Image.ANTIALIAS)
    image_right = get_save_file(stage2).resize(stage_size, Image.ANTIALIAS)
    # 定义圆角 蒙版
    _, image_alpha = circle_corner(image_left, radii=16)

    # 计算地图间隔
    width_between_stages = int((img_size[0] - 2 * stage_size[0]) / 3)
    # 绘制第一张地图
    # 图片左上点位
    start_stage_pos = (
        width_between_stages,
        int((img_size[1] - stage_size[1]) / 8 * 7) - 20,
    )
    image_background.paste(image_left, start_stage_pos, mask=image_alpha)
    # 绘制第二张地图
    # 图片左上点位
    next_stage_pos = (
        start_stage_pos[0] + width_between_stages + stage_size[0],
        start_stage_pos[1],
    )
    image_background.paste(image_right, next_stage_pos, mask=image_alpha)

    # 绘制地图中文名及文字背景
    # 左半地图名
    stage_name_bg = get_stage_name_bg(stage1.zh_name, 30)
    stage_name_bg_size = stage_name_bg.size
    # X:地图x点位+一半的地图宽度-文字背景的一半宽度   Y:地图Y点位+一半地图高度-文字背景高度
    stage_name_bg_pos = (
        start_stage_pos[0] + stage_size[0] // 2 - stage_name_bg_size[0] // 2,
        start_stage_pos[1] + stage_size[1] - stage_name_bg_size[1],
    )
    paste_with_a(image_background, stage_name_bg, stage_name_bg_pos)

    # 右半地图名
    stage_name_bg = get_stage_name_bg(stage2.zh_name, 30)
    stage_name_bg_size = stage_name_bg.size
    # X:地图x点位+一半的地图宽度-文字背景的一半宽度   Y:地图Y点位+一半地图高度-文字背景高度
    stage_name_bg_pos = (
        next_stage_pos[0] + +stage_size[0] // 2 - stage_name_bg_size[0] // 2,
        next_stage_pos[1] + stage_size[1] - stage_name_bg_size[1],
    )
    paste_with_a(image_background, stage_name_bg, stage_name_bg_pos)

    # 中间绘制 模式图标
    image_icon = get_file(contest_name)
    image_icon_size = image_icon.size
    # X: 整张卡片宽度/2 - 图标宽度/2    Y: 左地图x点位+地图高度/2 - 图标高度/2
    stage_mid_pos = (
        img_size[0] // 2 - image_icon_size[0] // 2,
        start_stage_pos[1] + stage_size[1] // 2 - image_icon_size[1] // 2,
    )
    paste_with_a(image_background, image_icon, stage_mid_pos)

    # 绘制模式文本
    # 空白尺寸
    blank_size = (img_size[0], start_stage_pos[1])
    drawer = ImageDraw.Draw(image_background)
    # 绘制竞赛模式文字
    ttf = ImageFont.truetype(ttf_path_chinese, 40)
    contest_mode_pos = (start_stage_pos[0] + 10, start_stage_pos[1] - 60)
    drawer.text(contest_mode_pos, contest_mode, font=ttf, fill=(255, 255, 255))
    # 绘制游戏模式文字
    game_mode_text = get_trans_game_mode(game_mode)
    game_mode_text_pos = (blank_size[0] // 3, contest_mode_pos[1])
    drawer.text(game_mode_text_pos, game_mode_text, font=ttf, fill=(255, 255, 255))
    # 绘制游戏模式小图标
    game_mode_img = get_file(game_mode_text).resize((35, 35), Image.ANTIALIAS)
    game_mode_img_pos = (game_mode_text_pos[0] - 40, game_mode_text_pos[1] + 10)
    paste_with_a(image_background, game_mode_img, game_mode_img_pos)
    # # 绘制开始，结束时间
    # ttf = ImageFont.truetype(ttf_path, 40)
    # time_pos = (blank_size[0] * 2 // 3, contest_mode_pos[1] - 10)
    # drawer.text(
    #     time_pos, "{} - {}".format(start_time, end_time), font=ttf, fill=(255, 255, 255)
    # )
    # 绘制活动模式描述
    if desc != "":
        ttf = ImageFont.truetype(ttf_path, 40)
        desc_pos = (blank_size[0] * 2 // 3, contest_mode_pos[1] - 10)
        drawer.text(desc_pos, desc, font=ttf, fill=(255, 255, 255))

    return image_background


# 绘制一排武器
def get_weapon_card(weapon: [WeaponData], weapon_card_bg_size, rgb):
    main_size = (120, 120)
    sub_size = (55, 55)
    special_size = (55, 55)
    # 单张武器背景
    weapon_bg_size = (150, 230)

    _, weapon_card_bg = circle_corner(Image.new("RGBA", weapon_card_bg_size, rgb), radii=20)

    # 遍历进行贴图
    for i, v in enumerate(weapon):
        v: WeaponData
        # 单张武器背景
        weapon_bg = Image.new("RGB", weapon_bg_size, rgb)
        _, weapon_bg = circle_corner(weapon_bg, radii=20)
        # 调整透明度
        weapon_bg = change_image_alpha(weapon_bg, 60)
        # 主武器
        main_image_bg = Image.new("RGBA", main_size, (30, 30, 30, 255))
        main_image = Image.open(io.BytesIO(v.image)).resize(main_size, Image.ANTIALIAS)
        main_image_bg_pos = ((weapon_bg_size[0] - main_size[0]) // 2, 10)
        # _, main_image = circle_corner(main_image, radii=16)
        # main_image_bg.paste(main_image, (0, 0))
        # 副武器
        sub_image_bg = Image.new("RGBA", sub_size, (60, 60, 60, 255))
        sub_image = Image.open(io.BytesIO(v.sub_image)).resize(sub_size, Image.ANTIALIAS)
        sub_image_bg_pos = (main_image_bg_pos[0], main_image_bg_pos[1] + main_size[1] + 10)
        # _, sub_image = circle_corner(sub_image, radii=16)
        # sub_image_bg.paste(sub_image, (0, 0))
        # 大招
        special_image_bg = Image.new("RGBA", special_size, (30, 30, 30, 255))
        special_image = Image.open(io.BytesIO(v.special_image)).resize(special_size, Image.ANTIALIAS)
        special_image_bg_pos = (main_image_bg_pos[0] + main_size[0] - special_size[0], sub_image_bg_pos[1])
        # _, special_image = circle_corner(special_image, radii=16)
        # special_image_bg.paste(special_image, (0, 0))
        # 贴到单个武器背景
        # weapon_bg.paste(main_image, main_image_bg_pos)
        # weapon_bg.paste(sub_image, sub_image_bg_pos)
        # weapon_bg.paste(special_image, special_image_bg_pos)

        paste_with_a(weapon_bg, main_image, main_image_bg_pos)
        paste_with_a(weapon_bg, sub_image, sub_image_bg_pos)
        paste_with_a(weapon_bg, special_image, special_image_bg_pos)

        # 武器名
        dr = ImageDraw.Draw(weapon_bg)
        font = ImageFont.truetype(ttf_path_chinese, 16)
        weapon_zh_name = v.zh_name
        zh_name_size = font.getsize(weapon_zh_name)
        # 文字居中
        zh_name_pos = ((weapon_bg_size[0] - zh_name_size[0]) // 2, weapon_bg_size[1] - zh_name_size[1] - 7)
        dr.text(zh_name_pos, weapon_zh_name, font=font, fill="#FFFFFF")
        # 将武器背景贴到武器区域
        # weapon_card_bg.paste(weapon_bg, ((weapon_bg_size[0]+10) * i + 10, 5))
        paste_with_a(
            weapon_card_bg,
            weapon_bg,
            ((weapon_bg_size[0] + 10) * i + 10, (weapon_card_bg_size[1] - weapon_bg_size[1]) // 2),
        )

    return weapon_card_bg


# 改变图片透明度  值为0-100
def change_image_alpha(image, transparency):
    image = image.convert("RGBA")
    alpha = image.split()[-1]
    alpha = alpha.point(lambda p: p * transparency // 100)
    new_image = Image.merge("RGBA", image.split()[:-1] + (alpha,))
    return new_image


# 绘制 活动地图卡片
def get_event_card(event, event_card_bg_size):
    # 背景
    event_card_bg = get_file("圆角").resize(event_card_bg_size).convert("RGBA")
    # 调整透明度
    event_card_bg = change_image_alpha(event_card_bg, 70)
    # 比赛卡片
    stage_card_pos = (10, 20)
    stage = event["leagueMatchSetting"]["vsStages"]
    stage_card = get_stage_card(
        ImageInfo(
            stage[0]["name"],
            stage[0]["image"]["url"],
            get_trans_stage(stage[0]["id"]),
            "对战地图",
        ),
        ImageInfo(
            stage[1]["name"],
            stage[1]["image"]["url"],
            get_trans_stage(stage[1]["id"]),
            "对战地图",
        ),
        "活动比赛",
        "活动比赛",
        event["leagueMatchSetting"]["vsRule"]["rule"],
    )
    stage_card_size = stage_card.size
    paste_with_a(event_card_bg, stage_card, stage_card_pos)
    # 绘制三个活动时间
    drawer = ImageDraw.Draw(event_card_bg)
    ttf = ImageFont.truetype(ttf_path_chinese, 40)
    pos_h = stage_card_pos[1] + stage_card_size[1] + 20
    for v in range(3):
        # 绘制游戏模式小图标
        game_mode_text = event["leagueMatchSetting"]["vsRule"]["rule"]
        game_mode_img_size = (35, 35)
        game_mode_img = get_file(game_mode_text).resize(game_mode_img_size, Image.ANTIALIAS)
        game_mode_img_pos = (20, pos_h)
        paste_with_a(event_card_bg, game_mode_img, game_mode_img_pos)
        # 绘制时间
        st = event["timePeriods"][v]["startTime"]
        et = event["timePeriods"][v]["endTime"]
        time_text_pos = (game_mode_img_pos[0] + game_mode_img_size[0] + 10, pos_h)
        time_text = "{} {}  {} - {} {}".format(
            time_converter_yd(st),
            "周" + dict_weekday_trans.get(time_converter_weekday(st)),
            time_converter_hm(st),
            time_converter_yd(et),
            time_converter_hm(et),
        )
        drawer.text(time_text_pos, time_text, font=ttf, fill=(255, 255, 255))
        # 绘制虚线
        transverse_line_pos = (game_mode_img_pos[0], game_mode_img_pos[1] + game_mode_img_size[1] + 20)
        # 开始与结束的xy坐标
        transverse_line_pos_list = [
            transverse_line_pos,
            (transverse_line_pos[0] + event_card_bg_size[0] - 50, transverse_line_pos[1]),
        ]
        draw_grid_transverse_line(drawer, transverse_line_pos_list, fill="white", width=3, gap=25)
        # 绘制 时间状态 文字
        now = datetime.datetime.now()
        if time_converter(st) > now:
            text = "未开始"
            text_color = (243, 254, 176)
        if time_converter(st) < now < time_converter(et):
            text = "进行中"
            text_color = (144, 203, 251)
        if time_converter(et) < now:
            text = "已结束"
            text_color = (165, 170, 163)
        text_size = ttf.getsize(text)
        drawer.text(
            (transverse_line_pos_list[1][0] - text_size[0] - 10, time_text_pos[1]),
            text,
            font=ttf,
            fill=text_color,
        )
        # 计算下一行高度
        pos_h += 80
    return event_card_bg


# 绘制 活动地图描述卡片
def get_event_desc_card(cht_event_data, event_desc_card_bg_size):
    # 背景
    event_desc_card_bg = get_file("圆角").resize(event_desc_card_bg_size).convert("RGBA")
    # 调整透明度
    event_desc_card_bg = change_image_alpha(event_desc_card_bg, 60)
    # 对规则文字分行
    desc = cht_event_data["desc"]
    regulation = cht_event_data["regulation"]
    regulation_list = regulation.split("<br />")
    # 绘制文本
    drawer = ImageDraw.Draw(event_desc_card_bg)
    ttf = ImageFont.truetype(ttf_path_chinese, 30)
    pos_h = 30
    for v in regulation_list:
        if v != "":
            text_pos = (20, pos_h)
            drawer.text(text_pos, v, font=ttf, fill=(255, 255, 255))
        pos_h += 40
    return event_desc_card_bg


# 画虚线 竖线
def draw_grid_vertical_line(draw, pos_list, fill, width, gap):
    x_begin, y_begin = pos_list[0]
    x_end, y_end = pos_list[1]
    for y in range(y_begin, y_end, gap):
        draw.line([(x_begin, y), (x_begin, y + gap / 2)], fill=fill, width=width)


# 画虚线 横线
def draw_grid_transverse_line(draw, pos_list, fill, width, gap):
    x_begin, y_begin = pos_list[0]
    x_end, y_end = pos_list[1]
    for x in range(x_begin, x_end, gap):
        draw.line([(x, y_begin), (x + gap / 2, y_begin)], fill=fill, width=width)


# 旧版函数 随机武器
# def old_get_random_weapon(weapon1: [] = None, weapon2: [] = None):
#     # 取两组随机武器
#     if weapon1 is None:
#         weapon1 = random.sample(os.listdir(weapon_folder), k=4)
#     if weapon2 is None:
#         weapon2 = random.sample(os.listdir(weapon_folder), k=4)
#     weapon_size = (122, 158)
#     _, image_background = circle_corner(get_file("背景").resize((620, 420)), radii=20)
#     dr = ImageDraw.Draw(image_background)
#     font = ImageFont.truetype(ttf_path, 50)
#     # 绘制中间vs和长横线
#     dr.text((278, 160), "VS", font=font, fill="#FFFFFF")
#     dr.line([(18, 210), (270, 210)], fill="#FFFFFF", width=4)
#     dr.line([(350, 210), (602, 210)], fill="#FFFFFF", width=4)
#     # 遍历进行贴图
#     for i in range(4):
#         image = get_weapon(weapon1[i]).resize(weapon_size, Image.ANTIALIAS)
#         image_background.paste(image, ((160 * i + 5), 20))
#         image = get_weapon(weapon2[i]).resize(weapon_size, Image.ANTIALIAS)
#         image_background.paste(image, ((160 * i + 5), 20 + 220))
#
#     return image_background


# 文本图片  弃用函数
# mode: coop,
# def draw_text_image(text, mode):
#     if mode == 'coop':
#         size = (960, 320)
#     elif mode == 'contest':
#         size = (960, 720)
#     else:
#         size = (1920, 1080)
#     img = Image.new("RGB", size, (255, 255, 255))
#     dr = ImageDraw.Draw(img)
#     font = ImageFont.truetype(ttf_path_chinese, 30)
#     dr.text((10, 5), text, font=font, fill="#000000")
#     return image_to_base64(img)

# if __name__ == '__main__':
#     get_random_weapon().show()