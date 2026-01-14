from PIL import Image
import os

def resize_and_pad(image_path, output_path, size=(900, 600)):
    # 画像を開く
    img = Image.open(image_path)
    
    # アスペクト比を維持してリサイズ
    img.thumbnail(size, Image.Resampling.LANCZOS)
    
    # 指定サイズの黒背景キャンバスを作成
    new_img = Image.new("RGB", size, (0, 0, 0))
    
    # 中央に配置
    offset = (
        (size[0] - img.size[0]) // 2,
        (size[1] - img.size[1]) // 2
    )
    new_img.paste(img, offset)
    
    # 保存
    new_img.save(output_path)
    print(f"Saved: {output_path}")

# 対象ファイルのリスト（ファイル名は適宜変更してください）
files = [
    "../images/LIMO.png",
    "../images/robot.png",
    "../images/spatial.png",
    "../images/security.png",
    "../images/human.png"
]

for i, f in enumerate(files):
    if os.path.exists(f):
        resize_and_pad(f, f"resized_900x600_{i+1}.png")