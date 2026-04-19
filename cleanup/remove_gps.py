import os
import glob
import tempfile
import shutil
import piexif

try:
    from PIL import Image
    import pillow_heif
    pillow_heif.register_heif_opener()
    has_heif = True
except ImportError:
    has_heif = False

def remove_gps_info_jpeg(file_path):
    try:
        exif_dict = piexif.load(file_path)
        if "GPS" in exif_dict and exif_dict["GPS"]:
            print(f"[{os.path.basename(file_path)}] GPS情報を削除して上書き保存しています...")
            exif_dict["GPS"] = {}
            exif_bytes = piexif.dump(exif_dict)
            # JPEGの場合は画質劣化なく直接Exifのみを書き換え可能
            piexif.insert(exif_bytes, file_path)
            return True
        else:
            print(f"[{os.path.basename(file_path)}] GPS情報はありません。スキップします。")
            return False
    except piexif.InvalidImageDataError:
        print(f"[{os.path.basename(file_path)}] Exif情報を読み込めない画像です。スキップします。")
        return False
    except Exception as e:
        print(f"[{os.path.basename(file_path)}] エラーが発生しました: {e}")
        return False

def remove_gps_info_heic(file_path):
    try:
        img = Image.open(file_path)
        if "exif" in img.info and img.info["exif"]:
            # HEICのExifデータをロード
            exif_dict = piexif.load(img.info["exif"])
            if "GPS" in exif_dict and exif_dict["GPS"]:
                print(f"[{os.path.basename(file_path)}] GPS情報を削除して上書き保存しています(HEIC)...")
                exif_dict["GPS"] = {}
                exif_bytes = piexif.dump(exif_dict)
                
                # 上書き時のアクセス競合を防ぐため、一時ファイルに保存してから置き換える
                fd, temp_path = tempfile.mkstemp(suffix=".heic")
                os.close(fd)
                try:
                    img.save(temp_path, "HEIF", exif=exif_bytes)
                    img.close()
                    shutil.move(temp_path, file_path)
                except Exception as e:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    print(f"[{os.path.basename(file_path)}] HEICの保存中にエラーが発生しました: {e}")
                    return False
                return True
            else:
                print(f"[{os.path.basename(file_path)}] GPS情報はありません。スキップします。")
                img.close()
                return False
        else:
            print(f"[{os.path.basename(file_path)}] Exif情報がありません。スキップします。")
            img.close()
            return False
    except Exception as e:
        print(f"[{os.path.basename(file_path)}] エラーが発生しました: {e}")
        return False


def remove_gps_info(target_dir):
    print("画像を検索中...")
    extensions = ('*.jpg', '*.jpeg', '*.JPG', '*.JPEG')
    if has_heif:
        extensions += ('*.heic', '*.HEIC')

    files = []
    for ext in extensions:
        files.extend(glob.glob(os.path.join(target_dir, ext)))

    if not files:
        print("指定されたフォルダに画像が見つかりませんでした。")
        return

    print(f"合計 {len(files)} 件の画像を処理します（上書き保存）...")
    
    for file_path in files:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.heic']:
            if has_heif:
                remove_gps_info_heic(file_path)
            else:
                print(f"[{os.path.basename(file_path)}] HEIC等処理モジュールがないためスキップします。")
        else:
            remove_gps_info_jpeg(file_path)

    print("-" * 30)
    print("すべての処理が完了しました。")

if __name__ == "__main__":
    target_directory = r"C:\Users\ytana\OneDrive\デスクトップ\amazon_photos"
    
    if not has_heif:
        print("※ HEIC形式をサポートするためのライブラリ 'pillow-heif' がインストールされていません。")
        print("※ HEIC画像を処理する場合はコマンドプロンプトで以下のコマンドを実行してください：")
        print("   pip install pillow-heif")
        print("-" * 50)
        
    remove_gps_info(target_directory)
