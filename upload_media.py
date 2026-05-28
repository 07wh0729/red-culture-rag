#!/usr/bin/env python3
"""
红色文化资源批量上传脚本
从 media/images/ 读取图片，通过 API 批量上传到平台
"""
import os
import sys
import requests
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_UPLOAD = f"{BASE_URL}/api/media/upload"

# 图片元信息：文件名 -> (标题, 标签)
IMAGE_META = {
    "01_red_boat.svg":       ("红船精神 · 南湖启航",    "红船精神,建党伟业,初心使命,1921"),
    "02_jinggangshan.svg":   ("井冈山精神 · 星火燎原",  "井冈山,星火燎原,革命根据地,1927"),
    "03_long_march.svg":     ("长征精神 · 万水千山",    "长征,红军,雪山草地,1934"),
    "04_yanan.svg":          ("延安精神 · 革命圣地",    "延安,宝塔,自力更生,1935"),
    "05_war_resistance.svg": ("抗战精神 · 血肉长城",    "抗日战争,民族精神,英雄,1937"),
    "06_xibaipo.svg":        ("西柏坡精神 · 进京赶考",  "西柏坡,两个务必,三大战役,1948"),
    "07_leifeng.svg":        ("雷锋精神 · 螺丝钉",      "雷锋,为人民服务,榜样,1963"),
    "08_two_bombs.svg":      ("两弹一星精神 · 科技强国", "两弹一星,钱学森,邓稼先,科技"),
    "09_reform.svg":         ("改革开放精神 · 春天故事", "改革开放,深圳,发展,1978"),
    "10_poverty_alleviation.svg": ("脱贫攻坚精神 · 不负人民", "脱贫攻坚,精准扶贫,小康,2020"),
}


def upload_image(filepath: str, title: str, tags: str) -> bool:
    """上传单张图片到平台"""
    try:
        with open(filepath, "rb") as f:
            files = {"file": (os.path.basename(filepath), f, "image/svg+xml")}
            data = {"title": title, "tags": tags}
            resp = requests.post(API_UPLOAD, files=files, data=data, timeout=30)
            if resp.status_code == 200:
                result = resp.json()
                print(f"  [OK] {os.path.basename(filepath)} -> {title}")
                return True
            else:
                print(f"  [FAIL] {os.path.basename(filepath)}: HTTP {resp.status_code} {resp.text[:100]}")
                return False
    except Exception as e:
        print(f"  [ERR] {os.path.basename(filepath)}: {e}")
        return False


def main():
    images_dir = Path(__file__).parent / "media" / "images"
    if not images_dir.exists():
        print(f"错误：图片目录不存在 {images_dir}")
        sys.exit(1)

    print("=" * 50)
    print("  红色文化资源批量上传")
    print("=" * 50)

    ok, fail = 0, 0
    for filename, (title, tags) in IMAGE_META.items():
        filepath = images_dir / filename
        if not filepath.exists():
            print(f"  [SKIP] {filename} 不存在")
            fail += 1
            continue
        if upload_image(str(filepath), title, tags):
            ok += 1
        else:
            fail += 1

    print("-" * 50)
    print(f"  完成: 成功 {ok} / 失败 {fail}")
    print("=" * 50)

    # 验证
    try:
        resp = requests.get(f"{BASE_URL}/api/media", timeout=10)
        if resp.status_code == 200:
            count = len(resp.json())
            print(f"\n当前资源库总计: {count} 件")
    except:
        pass


if __name__ == "__main__":
    main()
