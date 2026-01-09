# 壓縮圖片文檔，調整圖片的大小，轉換至JPG文檔
import os
import time
from PIL import Image # pyright: ignore[reportMissingImports]

# 處理 Pillow 版本相容性問題
try:
    # Pillow 10.0.0+
    LANCZOS = Image.Resampling.LANCZOS
except AttributeError:
    # Pillow < 10.0.0
    LANCZOS = Image.LANCZOS

# 核心功能: 圖片處理
class ImageProcessor:
    """負責核心的圖片處理邏輯。"""

    def process_batch(self, file_list, output_dir, output_format, quality=95, resize_options=None, progress_callback=None):
        """
        根據給定的設定批量處理圖片。

        Args:
            file_list (list): 圖片檔案的絕對路徑列表。
            output_dir (str): 儲存轉換後圖片的資料夾。
            output_format (str): 目標圖片格式 (例如 "PNG", "JPEG")。
            quality (int): JPEG 圖片的品質 (1-100)。
            resize_options (dict): 包含縮放選項的字典。
            progress_callback (function): 用於回報進度更新的函式，接收一個包含結果的字典。
        """
        total_files = len(file_list)
        processed_files = [] # 初始化已處理檔案列表
        for i, file_path in enumerate(file_list):
            start_time = time.time()
            original_filename = os.path.basename(file_path)
            progress_percent = ((i + 1) / total_files) * 100
            
            try:
                # 呼叫內部方法來轉換並儲存單一圖片，並獲取相關資訊
                result = self._convert_and_save(file_path, output_dir, output_format, quality, resize_options)
                new_filename = result["filename"]
                
                # 將完整的輸出路徑加入列表
                full_output_path = os.path.join(output_dir, new_filename)
                processed_files.append(full_output_path)

                duration = time.time() - start_time
                # 如果有提供進度回報函式，則回報成功結果
                if progress_callback:
                    callback_data = {
                        "filename": new_filename, # 在日誌中使用新的檔案名稱
                        "status": "success",
                        "duration": duration,
                        "message": "轉換成功",
                        "progress": progress_percent,
                        "original_size": result.get("original_size"),
                        "compressed_size": result.get("compressed_size")
                    }
                    progress_callback(callback_data)

            except Exception as e:
                duration = time.time() - start_time
                # 如果處理過程中發生錯誤，透過進度回報函式顯示錯誤訊息
                if progress_callback:
                    progress_callback({
                        "filename": original_filename, # 發生錯誤時，使用原始檔案名稱
                        "status": "failure",
                        "duration": duration,
                        "message": str(e),
                        "progress": progress_percent
                    })
        
        # 所有檔案處理完畢後，回報處理完成
        if progress_callback:
            progress_callback({"status": "finished", "progress": 100, "message": "批量處理完成。", "output_files": processed_files})

    def _convert_and_save(self, input_path, output_dir, output_format, quality, resize_options):
        """
        轉換、縮放並儲存單一圖片。
        """
        # 如果輸出資料夾不存在，則建立它
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        try:
            # 標準化路徑，確保跨平台相容性
            normalized_path = os.path.normpath(input_path)
            
            # 獲取原始大小
            original_size = os.path.getsize(normalized_path)

            # 使用 'with open' 來開啟檔案，可以更好地處理路徑問題
            with open(normalized_path, 'rb') as f:
                img = Image.open(f)
                # 確保在檔案關閉前載入圖片資料
                img.load()
            
            # 處理透明度問題：如果目標格式不支援透明度 (如 JPEG, BMP)，且圖片有 RGBA/P 模式，則轉換為 RGB
            output_format_upper = output_format.upper()
            if output_format_upper in ['JPEG', 'BMP'] and (img.mode == 'RGBA' or img.mode == 'P'):
                img = img.convert('RGB')

            # 圖片縮放
            if resize_options and resize_options.get('type') != 'none':
                img = self._resize_image(img, resize_options)

            # 準備輸出路徑
            base_name = os.path.basename(input_path)
            file_name, _ = os.path.splitext(base_name)
            output_path = os.path.join(output_dir, f"{file_name}.{output_format.lower()}")

            # 準備儲存選項
            save_options = {}
            if output_format.upper() == 'JPEG':
                save_options['quality'] = quality
            elif output_format.upper() == 'GIF':
                save_options['optimize'] = True
            
            # 儲存圖片
            img.save(output_path, format=output_format, **save_options)

            # 獲取壓縮後大小
            compressed_size = os.path.getsize(output_path)

            # 回傳詳細資訊
            return {
                "filename": os.path.basename(output_path),
                "original_size": original_size,
                "compressed_size": compressed_size
            }

        except Exception as e:
            # 將錯誤向上拋出，由外層的 process_batch 捕捉
            raise e

    def _resize_image(self, img, resize_options):
        """
        根據提供的選項縮放圖片。
        """
        resize_type = resize_options.get('type')
        
        # 按比例縮放
        if resize_type == 'scale':
            scale_percent = resize_options.get('value', 100)
            new_width = int(img.width * scale_percent / 100)
            new_height = int(img.height * scale_percent / 100)
            return img.resize((new_width, new_height), LANCZOS)
            
        # 按固定尺寸縮放
        elif resize_type == 'fixed':
            width = resize_options.get('width')
            height = resize_options.get('height')
            if width and height:
                return img.resize((width, height), LANCZOS)
                
        return img
