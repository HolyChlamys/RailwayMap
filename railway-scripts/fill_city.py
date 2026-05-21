#!/usr/bin/env python3
"""
Fill stations.city from station name by matching against known Chinese city names.

Strategy:
1. Try exact prefix match (longest first) against prefecture-level city list
2. For stations with common suffixes (站, 南站, 北站等), strip suffix then match
3. Fall back: use 2-3 character prefix match
"""

import psycopg2
import re

# Comprehensive list of Chinese prefecture-level cities + major county-level cities
# Provincial capitals and major railway hub cities prioritized
CITIES = sorted([
    # Municipalities
    "北京", "上海", "天津", "重庆",
    # Provinces - capitals + prefectures
    # Anhui
    "合肥", "芜湖", "蚌埠", "淮南", "马鞍山", "淮北", "铜陵", "安庆", "黄山",
    "滁州", "阜阳", "宿州", "六安", "亳州", "池州", "宣城",
    # Fujian
    "福州", "厦门", "莆田", "三明", "泉州", "漳州", "南平", "龙岩", "宁德",
    # Gansu
    "兰州", "嘉峪关", "金昌", "白银", "天水", "武威", "张掖", "平凉", "酒泉", "庆阳", "定西", "陇南", "临夏", "甘南",
    # Guangdong
    "广州", "韶关", "深圳", "珠海", "汕头", "佛山", "江门", "湛江", "茂名",
    "肇庆", "惠州", "梅州", "汕尾", "河源", "阳江", "清远", "东莞", "中山", "潮州", "揭阳", "云浮",
    # Guangxi
    "南宁", "柳州", "桂林", "梧州", "北海", "防城港", "钦州", "贵港", "玉林", "百色", "贺州", "河池", "来宾", "崇左",
    # Guizhou
    "贵阳", "六盘水", "遵义", "安顺", "毕节", "铜仁", "黔西南", "黔东南", "黔南",
    # Hainan
    "海口", "三亚", "三沙", "儋州",
    # Hebei
    "石家庄", "唐山", "秦皇岛", "邯郸", "邢台", "保定", "张家口", "承德", "沧州", "廊坊", "衡水",
    # Henan
    "郑州", "开封", "洛阳", "平顶山", "安阳", "鹤壁", "新乡", "焦作", "濮阳", "许昌", "漯河", "三门峡", "南阳", "商丘", "信阳", "周口", "驻马店", "济源",
    # Heilongjiang
    "哈尔滨", "齐齐哈尔", "鸡西", "鹤岗", "双鸭山", "大庆", "伊春", "佳木斯", "七台河", "牡丹江", "黑河", "绥化", "大兴安岭",
    # Hubei
    "武汉", "黄石", "十堰", "宜昌", "襄阳", "鄂州", "荆门", "孝感", "荆州", "黄冈", "咸宁", "随州", "恩施", "仙桃", "潜江", "天门", "神农架",
    # Hunan
    "长沙", "株洲", "湘潭", "衡阳", "邵阳", "岳阳", "常德", "张家界", "益阳", "郴州", "永州", "怀化", "娄底", "湘西",
    # Inner Mongolia
    "呼和浩特", "包头", "乌海", "赤峰", "通辽", "鄂尔多斯", "呼伦贝尔", "巴彦淖尔", "乌兰察布", "兴安", "锡林郭勒", "阿拉善",
    # Jiangsu
    "南京", "无锡", "徐州", "常州", "苏州", "南通", "连云港", "淮安", "盐城", "扬州", "镇江", "泰州", "宿迁",
    # Jiangxi
    "南昌", "景德镇", "萍乡", "九江", "新余", "鹰潭", "赣州", "吉安", "宜春", "抚州", "上饶",
    # Jilin
    "长春", "吉林", "四平", "辽源", "通化", "白山", "松原", "白城", "延边", "延吉", "珲春", "图们", "敦化",
    # Liaoning
    "沈阳", "大连", "鞍山", "抚顺", "本溪", "丹东", "锦州", "营口", "阜新", "辽阳", "盘锦", "铁岭", "朝阳", "葫芦岛",
    # Ningxia
    "银川", "石嘴山", "吴忠", "固原", "中卫",
    # Qinghai
    "西宁", "海东", "海北", "黄南", "海南", "果洛", "玉树", "海西", "格尔木",
    # Shaanxi
    "西安", "铜川", "宝鸡", "咸阳", "渭南", "延安", "汉中", "榆林", "安康", "商洛",
    # Shandong
    "济南", "青岛", "淄博", "枣庄", "东营", "烟台", "潍坊", "济宁", "泰安", "威海", "日照", "临沂", "德州", "聊城", "滨州", "菏泽",
    # Shanxi
    "太原", "大同", "阳泉", "长治", "晋城", "朔州", "晋中", "运城", "忻州", "临汾", "吕梁",
    # Sichuan
    "成都", "自贡", "攀枝花", "泸州", "德阳", "绵阳", "广元", "遂宁", "内江", "乐山", "南充", "眉山", "宜宾", "广安", "达州", "雅安", "巴中", "资阳", "阿坝", "甘孜", "凉山", "西昌",
    # Tibet
    "拉萨", "日喀则", "昌都", "林芝", "山南", "那曲", "阿里",
    # Xinjiang
    "乌鲁木齐", "克拉玛依", "吐鲁番", "哈密", "昌吉", "博尔塔拉", "巴音郭楞", "阿克苏", "克孜勒苏", "喀什", "和田", "伊犁", "塔城", "阿勒泰", "石河子", "阿拉尔", "图木舒克", "五家渠", "北屯", "铁门关", "双河", "可克达拉", "昆玉", "胡杨河",
    # Yunnan
    "昆明", "曲靖", "玉溪", "保山", "昭通", "丽江", "普洱", "临沧", "楚雄", "红河", "文山", "西双版纳", "大理", "德宏", "怒江", "迪庆",
    # Zhejiang
    "杭州", "宁波", "温州", "嘉兴", "湖州", "绍兴", "金华", "衢州", "舟山", "台州", "丽水",
    # Hong Kong / Macau
    "香港", "澳门",
    # Additional major county-level cities / railway hubs
    "义乌", "昆山", "江阴", "张家港", "常熟", "太仓", "宜兴", "溧阳", "丹阳", "扬中", "句容",
    "海宁", "慈溪", "余姚", "奉化", "瑞安", "乐清", "诸暨", "嵊州", "江山", "龙泉",
    "晋江", "石狮", "南安", "福清", "长乐", "龙海", "邵武", "永安", "漳平",
    "荣成", "文登", "乳山", "寿光", "诸城", "安丘", "高密", "昌邑", "曲阜",
    "新郑", "登封", "巩义", "荥阳", "新密", "偃师", "汝州", "舞钢", "林州",
    "大冶", "宜都", "当阳", "枝江", "老河口", "枣阳", "广水", "丹江口",
    "涿州", "定州", "辛集", "藁城", "晋州", "新乐", "遵化", "迁安", "武安", "南宫", "沙河",
    "高碑店", "安国", "泊头", "任丘", "黄骅", "河间", "霸州", "三河", "冀州", "深州",
    "肇东", "安达", "五常", "尚志", "讷河", "密山", "虎林", "铁力", "绥芬河", "宁安", "海林", "穆棱",
    "大丰", "东台", "邳州", "新沂", "仪征", "高邮", "兴化", "靖江", "泰兴",
    "兰溪", "永康", "临海", "温岭", "建德", "富阳", "临安", "平湖", "桐乡",
    "长葛", "禹州", "辉县", "卫辉", "沁阳", "孟州", "永城", "项城",
    "英德", "连州", "乐昌", "南雄", "兴宁", "陆丰", "阳春", "高州", "化州", "信宜",
    "岑溪", "东兴", "桂平", "北流", "靖西", "宜州",
    "万宁", "文昌", "琼海", "五指山", "东方",
    "阆中", "华蓥", "万源", "简阳", "峨眉山", "崇州", "邛崃", "都江堰", "彭州",
    "仁怀", "赤水", "都匀", "福泉", "凯里", "镇远",
    "安宁", "宣威", "腾冲", "楚雄", "个旧", "蒙自", "弥勒", "开远",
    "兴平", "韩城", "华阴", "神木", "府谷", "靖边",
    "敦煌", "玉门", "合作", "夏河",
    "灵武", "青铜峡",
    "青铜峡", "盐池",
    "格尔木", "德令哈",
    "塔城", "乌苏", "沙湾", "额敏",
    "尉犁", "轮台", "且末", "若羌", "焉耆",
    # More rail hubs
    "丰台", "海淀", "朝阳", "通州", "大兴", "房山", "门头沟", "昌平", "石景山",
    "虹桥", "浦东",
    "呈贡", "晋宁", "东川",
    "白云", "花都", "番禺", "南沙", "增城", "从化",
    "武进", "金坛",
    "嘉定", "松江", "青浦", "奉贤", "崇明",
    "璧山", "长寿", "合川", "永川", "南川", "綦江", "大足", "铜梁", "潼南", "荣昌", "开州", "梁平", "武隆",
    "即墨", "平度", "莱西", "胶州",
    "肥东", "肥西", "长丰", "庐江", "巢湖",
    "南昌县", "进贤", "安义",
    "鹿泉", "栾城", "正定",
    "乌伊岭", "伊春",
    # Additional towns/cities that are station name prefixes
], key=len, reverse=True)  # Sort by length descending for longest-match-first

# Common station name suffixes to strip before matching
SUFFIXES = [
    "南站", "北站", "东站", "西站", "火车站", "高铁站",
    "南", "北", "东", "西", "站",
    "新站", "老站", "客站", "货站",
    "南广场", "北广场",
]

def extract_city(station_name: str) -> str | None:
    """Try to extract city name from station name."""
    if not station_name:
        return None

    name = station_name.strip()

    # Try exact city match (longest first)
    for city in CITIES:
        if name.startswith(city):
            # Must not be a coincidental prefix match
            remainder = name[len(city):]
            # Accept if remainder is empty or a known suffix pattern
            if len(remainder) == 0:
                return city
            if any(remainder == s for s in SUFFIXES):
                return city
            if re.match(r'^[东西南北站]?$', remainder):
                return city
            # If remainder starts with a known suffix-like pattern
            if remainder in ['东', '西', '南', '北', '站'] or remainder == '':
                return city
            # Accept any 1-2 char remainder that doesn't form another city name
            if len(remainder) <= 1:
                return city
            # For longer remainders, check if remainder is purely a suffix
            if re.match(r'^(南|北|东|西)?(站|场|线|广场|东站|西站|南站|北站)$', remainder):
                return city

    # Try stripping known suffixes first, then match
    for suffix in SUFFIXES:
        if name.endswith(suffix):
            base = name[:-len(suffix)]
            if base:
                result = extract_city(base)
                if result:
                    return result

    return None


def main():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        user="railway",
        password="railway123",
        database="railwaymap"
    )
    conn.autocommit = False
    cur = conn.cursor()

    # Fetch all stations without city
    cur.execute("SELECT id, name FROM stations WHERE city IS NULL OR city = ''")
    stations = cur.fetchall()
    print(f"Stations to process: {len(stations)}")

    matched = 0
    unmatched = []
    updates = []

    for sid, name in stations:
        city = extract_city(name)
        if city:
            updates.append((city, sid))
            matched += 1
        else:
            unmatched.append((sid, name))

    # Batch update
    if updates:
        cur.executemany(
            "UPDATE stations SET city = %s WHERE id = %s",
            updates
        )
        conn.commit()
        print(f"Updated {matched} stations with city")

    if unmatched:
        print(f"Unmatched: {len(unmatched)} stations")
        # Show first 50 unmatched for review
        for sid, name in unmatched[:50]:
            print(f"  [{sid}] {name}")

    # Also update the city column for train_stops' station_name-based queries
    # by copying city from matched stations

    cur.close()
    conn.close()
    print("Done")


if __name__ == "__main__":
    main()
