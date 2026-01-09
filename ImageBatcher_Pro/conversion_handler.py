#後台排程器
import threading
from image_processor import ImageProcessor

def run_conversion_in_thread(settings):
    """
    在獨立的執行緒中初始化並執行圖片批次處理。

    這個函式會建立一個 ImageProcessor 的實體，
    並在一個新的背景執行緒中呼叫其 process_batch 方法，
    以避免 GUI 阻塞。

    Args:
        settings (dict): 包含處理所需所有設定的字典，
                         例如 file_list, output_dir, progress_callback 等。
    """
    processor = ImageProcessor()

    def processing_job():
        """這是執行緒實際執行的工作。"""
        try:
            # 將設定解包並傳遞給 process_batch 方法
            processor.process_batch(**settings)
        except Exception as e:
            # 在實際應用中，這裡可能需要一個更完善的錯誤回報機制，
            # 例如透過回呼函式將錯誤訊息傳回 GUI。
            print(f"處理執行緒中發生未預期的錯誤: {e}")
            # 如果有回呼函式，也可以用來通知 GUI 發生錯誤
            if 'progress_callback' in settings:
                error_info = {
                    "status": "error",
                    "message": str(e)
                }
                settings['progress_callback'](error_info)

    # 建立並啟動 daemon 執行緒
    # daemon 執行緒會隨著主程式的退出而自動結束
    thread = threading.Thread(target=processing_job)
    thread.daemon = True
    thread.start()
