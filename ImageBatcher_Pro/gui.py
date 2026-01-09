# 裁剪圖片，旋轉圖片
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import datetime
import zipfile
import time
from PIL import Image, ImageTk, ImageSequence # type: ignore
from ttkthemes import ThemedTk # type: ignore

# 從 image_processor 模組匯入 ImageProcessor 類別
from image_processor import ImageProcessor
# 從 conversion_handler 模組匯入執行緒轉換函式
from conversion_handler import run_conversion_in_thread
# 從 video_processor 模組匯入 VideoProcessor 類別
from video_processor import VideoProcessor


# 主應用程式類別，繼承自 ThemedTk 以使用主題
class App(ThemedTk):
    """主要的 GUI 應用程式視窗。"""

    def __init__(self):
        # --- 初始化視窗 ---
        super().__init__(theme="arc")

            
        self.title("Python柏融自製批量圖片轉換小小工具")
        self.geometry("800x650") # 增加高度以容納新按鈕

        # --- 定義字體和顏色 ---
        self.font_family = "Segoe UI"
        self.font_normal = (self.font_family, 10)
        self.font_bold = (self.font_family, 10, "bold")
        self.accent_color = "#5294e2"

        # --- 設定 ttk 元件的全域樣式 ---
        self.style = ttk.Style(self)
        self.style.configure("TLabel", font=self.font_normal)
        self.style.configure("TButton", font=self.font_bold)
        self.style.configure("TLabelFrame.Label", font=self.font_bold)
        self.style.configure("TRadiobutton", font=self.font_normal)
        self.style.configure("Accent.TButton", font=self.font_bold)
        self.style.configure("Large.TButton", font=(self.font_family, 14, "bold"), padding=15, foreground="#4285f4")
        self.style.configure("Blue.TButton", font=self.font_bold, foreground="black")

        # --- 初始化變數 ---
        self.file_list = []
        self.converted_files = []
        self.output_dir = ""
        self.processor = ImageProcessor()
        self.video_processor = VideoProcessor() # 初始化影片處理器

        self.file_list_frame = None
        self.file_list_frame = None
        
        # 裁剪相關變數
        self.crop_image = None
        self.crop_image_tk = None
        
        # 影片播放相關變數
        self.is_playing = False
        self.play_job = None
        
        self.display_scale = 1.0

        self.display_scale = 1.0
        self.crop_vars = {
            "width": tk.IntVar(),
            "height": tk.IntVar(),

            "width": tk.IntVar(),
            "height": tk.IntVar(),
            "x": tk.IntVar(),
            "y": tk.IntVar()
        }
        self.drag_data = {"x": 0, "y": 0, "mode": None} # 用於拖曳操作
        
        # 調整大小變數
        self.resize_image = None




        # --- 主體介面佈局 ---
        # 建立主容器，用於切換首頁和工具視圖
        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # 建立首頁框架
        self.home_frame = ttk.Frame(self.main_container)
        
        # 建立工具視圖容器
        self.tools_container = ttk.Frame(self.main_container)
        
        # 在工具容器中添加返回首頁的標題欄
        self.tools_header = ttk.Frame(self.tools_container)
        self.tools_header.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        # 返回首頁按鈕
        self.btn_home = ttk.Button(self.tools_header, text="🏠 返回首頁", command=self._show_home, style="Accent.TButton")
        self.btn_home.pack(side=tk.LEFT)
        
        # 使用 Notebook 建立分頁導覽
        self.notebook = ttk.Notebook(self.tools_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

        # 建立各個分頁
        self.compress_tab = ttk.Frame(self.notebook)
        self.resize_tab = ttk.Frame(self.notebook)
        self.crop_tab = ttk.Frame(self.notebook)
        self.convert_tab = ttk.Frame(self.notebook)
        self.rotate_tab = ttk.Frame(self.notebook)
        self.video_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.compress_tab, text="壓縮圖片文檔")
        self.notebook.add(self.resize_tab, text="調整圖片的大小")
        self.notebook.add(self.crop_tab, text="裁剪圖片")
        self.notebook.add(self.convert_tab, text="轉換至JPG文檔")
        self.notebook.add(self.rotate_tab, text="旋轉圖片")
        self.notebook.add(self.video_tab, text="影片截圖")

        # --- 初始化所有分頁內容 ---
        self._create_convert_tab_content(self.convert_tab)
        self._create_compress_tab_content(self.compress_tab)
        self._create_resize_tab_content(self.resize_tab)
        self._create_crop_tab_content(self.crop_tab)
        self._create_rotate_tab_content(self.rotate_tab)
        self._create_video_tab_content(self.video_tab)
        
        # --- 初始化首頁儀表板 ---
        self.selection_mode_active = False # 新增：用於追蹤是否進入壓縮選擇模式
        
        # --- GIF 動畫狀態 ---
        self._gif_animations = {} # label/canvas -> {cancel_id, frames}

        self._create_home_dashboard()
        self._show_home()


    def _show_home(self):
        """顯示首頁儀表板"""
        self.tools_container.pack_forget()
        self.home_frame.pack(fill=tk.BOTH, expand=True)
    
    def _show_tool(self, tab_index):
        """顯示工具視圖並切換到指定分頁"""
        self.home_frame.pack_forget()
        self.tools_container.pack(fill=tk.BOTH, expand=True)
        self.notebook.select(tab_index)
    
    def _create_home_dashboard(self):
        """建立首頁儀表板，包含工具選擇卡片"""
        # 清空舊內容
        for widget in self.home_frame.winfo_children():
            widget.destroy()
        
        # 標題區
        title_frame = ttk.Frame(self.home_frame)
        title_frame.pack(pady=(40, 10))
        
        title = ttk.Label(title_frame, text="可批量編輯圖片的所有工具", 
                         font=(self.font_family, 28, "bold"), foreground="#333")
        title.pack()
        
        # 工具卡片區
        cards_container = ttk.Frame(self.home_frame)
        cards_container.pack(fill=tk.BOTH, expand=True, padx=60, pady=30)
        
        # 定義工具卡片資料: (名稱, 描述, 圖標, 分頁索引, 背景色)
        tools = [
            ("壓縮圖片文檔", "壓縮 JPG, PNG或GIF，\n並保持最佳質量。", "📦", 0, "#e8f5e9"),
            ("調整圖片的大小", "以像素或百分比定義尺寸。\n縮放 JPG, PNG, GIF 文檔。", "🔧", 1, "#e3f2fd"),
            ("裁剪圖片", "通過像素設定範圍，裁剪\nJPG, PNG 或 GIF 文檔。", "✂️", 2, "#fff3e0"),
            ("轉換至JPG文檔", "將圖片轉換為 JPG 格式，\n支持多種輸入格式。", "🔄", 3, "#f3e5f5"),
            ("旋轉圖片", "旋轉 JPG, PNG 或 GIF，\n每次旋轉 90° 或 180°。", "↻", 4, "#fff9c4"),
            ("影片截圖", "從影片中擷取畫面，\n保存為圖片檔案。", "🎬", 5, "#fce4ec"),
        ]
        
        # 建立卡片網格（每行3個）
        row = 0
        col = 0
        max_cols = 3
        
        for name, desc, icon, tab_idx, bg_color in tools:
            card = self._create_tool_card(cards_container, name, desc, icon, tab_idx, bg_color)
            # 移除 sticky 讓卡片自然居中，不要延展
            card.grid(row=row, column=col, padx=15, pady=15)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
        
        # 設定網格權重以實現均勻分佈
        for i in range(max_cols):
            cards_container.grid_columnconfigure(i, weight=1, uniform="cards")
        for i in range((len(tools) + max_cols - 1) // max_cols):
            cards_container.grid_rowconfigure(i, weight=0)
    
    def _create_tool_card(self, parent, name, desc, icon, tab_index, bg_color):
        """建立單個工具卡片"""
        # 使用 Canvas 來繪製卡片，提供更好的樣式控制
        card_frame = tk.Frame(parent, bg="#f5f5f5", width=284, height=204)
        card_frame.pack_propagate(False)  # 防止內容改變框架大小
        
        canvas = tk.Canvas(card_frame, width=280, height=200, bg=bg_color, 
                          highlightthickness=2, highlightbackground="#ddd", cursor="hand2")
        canvas.pack(padx=2, pady=2)
        
        # 繪製圖標
        canvas.create_text(140, 50, text=icon, font=("Arial", 48), fill="#333")
        
        # 繪製標題
        canvas.create_text(140, 110, text=name, font=(self.font_family, 14, "bold"), fill="#333")
        
        # 繪製描述
        canvas.create_text(140, 155, text=desc, font=(self.font_family, 10), 
                          fill="#555", justify="center")
        
        # 綁定點擊事件
        canvas.bind("<Button-1>", lambda e: self._show_tool(tab_index))
        
        # 懸停效果
        def on_enter(e):
            canvas.configure(highlightbackground="#4285f4", highlightthickness=3)
            canvas.configure(bg=self._lighten_color(bg_color))
        
        def on_leave(e):
            canvas.configure(highlightbackground="#ddd", highlightthickness=2)
            canvas.configure(bg=bg_color)
        
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        
        return card_frame
    
    def _lighten_color(self, hex_color):
        """將顏色調亮一些（簡單實現）"""
        # 簡化版本：返回白色
        return "#ffffff"

    def _create_placeholder_tab(self, parent, text):
        label = ttk.Label(parent, text=text, font=self.font_bold)
        label.pack(expand=True)

    def _create_blue_button(self, parent, text, command, height=45, width=None):
        """Creates a blue rectangular canvas button similar to the Resize tab's save button."""
        # Custom Canvas Button
        btn_canvas = tk.Canvas(parent, height=height, bg="#4285f4", highlightthickness=0, cursor="hand2")
        if width:
            btn_canvas.configure(width=width)
            
        # Draw Text
        # We need to center text. We can do this initially, and bind configure for robust centering.
        text_id = btn_canvas.create_text(0, 0, text=text, fill="black", font=(self.font_family, 11, "bold"), anchor="center")
        
        def _center_text(event):
            w, h = event.width, event.height
            btn_canvas.coords(text_id, w/2, h/2)
            
        btn_canvas.bind("<Configure>", _center_text)
        btn_canvas.bind("<Button-1>", lambda e: command())
        
        return btn_canvas

    def _reset_crop_tab(self):
        if hasattr(self, 'crop_canvas'):
            self._stop_animation(self.crop_canvas)
        for widget in self.crop_tab.winfo_children():
            widget.destroy()
        self.crop_image = None
        self._create_crop_tab_content(self.crop_tab)

    def _create_crop_tab_content(self, parent):
        # 建立置中容器
        center_frame = ttk.Frame(parent)
        center_frame.place(relx=0.5, rely=0.4, anchor="center")

        # 標題
        title_label = ttk.Label(center_frame, text="裁剪圖片", font=(self.font_family, 24, "bold"))
        title_label.pack(pady=(0, 15))

        # 描述文字
        desc_text = "通過像素設定範圍，裁剪 JPG文檔, PNG文檔 或 GIF文檔。\n線上裁剪你的圖片文檔。"
        desc_label = ttk.Label(center_frame, text=desc_text, justify="center", font=(self.font_family, 11))
        desc_label.pack(pady=(0, 30))

        # 按鈕容器
        btn_frame = ttk.Frame(center_frame)
        btn_frame.pack()

        # 大按鈕 (模擬樣式)
        # 注意: ttk 在某些主題下修改背景色較困難，這裡使用自定義樣式
        # self.style.configure("Large.TButton", font=(self.font_family, 14, "bold"), padding=15)
        
        select_btn = ttk.Button(btn_frame, text="選擇多張圖片", style="Large.TButton", command=self._select_crop_images)
        select_btn.pack(side="left", padx=5)

        # 圓形圖標按鈕 (暫時用文字代替圖標)
        # drive_btn = ttk.Button(btn_frame, text="云", width=3)
        # drive_btn.pack(side="left", padx=2)
        # dropbox_btn = ttk.Button(btn_frame, text="盒", width=3) 
        # dropbox_btn.pack(side="left", padx=2)

        # 底部文字
        bottom_label = ttk.Label(center_frame, text="或者將多張圖片拖動到這裏", font=(self.font_family, 9), foreground="gray")
        bottom_label.pack(pady=(15, 0))

    def _select_crop_images(self):
        files = filedialog.askopenfilenames(title="選擇圖片", filetypes=[("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.webp *.gif")])
        if files:
            # 這裡我們只取第一張圖片進行編輯
            self._crop_file_path = files[0]
            self._load_image_on_canvas(files[0])
            self._switch_to_crop_editor()

    def _switch_to_crop_editor(self):
        # 清空 crop_tab
        for widget in self.crop_tab.winfo_children():
            widget.destroy()
        self._create_crop_editor_ui(self.crop_tab)

    def _create_crop_editor_ui(self, parent):
        # 左右佈局
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左側畫布
        self.crop_canvas = tk.Canvas(paned, bg='#e0e0e0')
        paned.add(self.crop_canvas, weight=3)
        
        # 綁定滑鼠事件
        self.crop_canvas.bind("<Button-1>", self._on_crop_press)
        self.crop_canvas.bind("<B1-Motion>", self._on_crop_drag)
        self.crop_canvas.bind("<ButtonRelease-1>", self._on_crop_release)

        # 右側設定面板
        settings_frame = ttk.Frame(paned, padding="10")
        paned.add(settings_frame, weight=1)

        # 設定面板內容
        ttk.Label(settings_frame, text="裁剪選項", font=(self.font_family, 14, "bold")).pack(pady=(0, 20))

        # 輸入欄位建立函式
        def create_input(label_text, var_name):
            frame = ttk.Frame(settings_frame)
            frame.pack(fill=tk.X, pady=10)
            ttk.Label(frame, text=label_text).pack(anchor="w")
            spin = ttk.Spinbox(frame, from_=0, to=9999, textvariable=self.crop_vars[var_name], command=self._update_crop_preview)
            spin.pack(fill=tk.X)
            spin.bind("<KeyRelease>", self._update_crop_preview) # 綁定鍵盤輸入
            return spin

        create_input("寬度 (px)", "width")
        create_input("高度 (px)", "height")
        create_input("位置 X (px)", "x")
        create_input("位置 Y (px)", "y")

        # 底部按鈕
        # ttk.Button(settings_frame, text="裁剪圖片", style="Accent.TButton", command=self._perform_crop_and_save).pack(side=tk.BOTTOM, fill=tk.X, pady=20)
        self._create_blue_button(settings_frame, "裁剪圖片", self._perform_crop_and_save).pack(side=tk.BOTTOM, fill=tk.X, pady=20)

        # 繪製 Canvas 內容
        self._draw_canvas_content()

    def _perform_crop_and_save(self):
        if not self.crop_image:
            return

        try:
            x = self.crop_vars["x"].get()
            y = self.crop_vars["y"].get()
            w = self.crop_vars["width"].get()
            h = self.crop_vars["height"].get()
        except tk.TclError:
            messagebox.showerror("錯誤", "無效的數值輸入")
            return

        # 基本驗證
        img_w, img_h = self.crop_image.size
        if w <= 0 or h <= 0:
            messagebox.showerror("錯誤", "裁剪寬度與高度必須大於 0")
            return
            
        # 執行裁剪
        try:
            # Pillow crop: (left, top, right, bottom)
            box = (x, y, x + w, y + h)
            cropped_img = self.crop_image.crop(box)
            
            # 詢問儲存位置
            # 詢問儲存位置
            file_path = filedialog.asksaveasfilename(
                title="儲存裁剪後的圖片",
                defaultextension=".jpg",
                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("GIF", "*.gif"), ("All Files", "*.*")]
            )
            
            if file_path:
                if file_path.lower().endswith('.gif'):
                    # 儲存為動態 GIF
                    frames = []
                    # 使用原始圖片取得完整動畫影格
                    # 注意：self.crop_image 是已開啟的圖片物件
                    duration = self.crop_image.info.get('duration', 100)
                    try:
                        for frame in ImageSequence.Iterator(self.crop_image):
                            f = frame.copy().convert('RGBA')
                            f = f.crop(box)
                            frames.append(f)
                        
                        if frames:
                            frames[0].save(file_path, save_all=True, append_images=frames[1:], loop=0, duration=duration, optimize=False, disposal=2)
                        else:
                            # 若找不到影格則使用備案
                            cropped_img.save(file_path)
                    except Exception as e:
                        # 若迭代失敗則使用單一影格備案
                        print(f"GIF save error: {e}")
                        cropped_img.save(file_path)
                else:
                    cropped_img.save(file_path)
                
                messagebox.showinfo("成功", f"圖片已儲存至:\n{file_path}")
                self._reset_crop_tab()
                
        except Exception as e:
            messagebox.showerror("錯誤", f"裁剪或儲存失敗:\n{e}")

    def _load_image_on_canvas(self, file_path):
        if hasattr(self, 'crop_canvas'):
            self._stop_animation(self.crop_canvas)
        self.crop_image = Image.open(file_path)
        
        # 初始化裁剪框 (預設為圖片的一半大小，置中)
        w, h = self.crop_image.size
        self.crop_vars["width"].set(w // 2)
        self.crop_vars["height"].set(h // 2)
        self.crop_vars["x"].set(w // 4)
        self.crop_vars["y"].set(h // 4)
        

    def _draw_canvas_content(self):
        if not self.crop_image:
            return

        # 強制更新 UI 以便獲取正確的 Canvas 大小
        self.crop_canvas.update_idletasks()
        
        canvas_width = self.crop_canvas.winfo_width()
        canvas_height = self.crop_canvas.winfo_height()
        
        # 如果還是太小 (尚未顯示)，使用預設值
        if canvas_width <= 1: canvas_width = 800
        if canvas_height <= 1: canvas_height = 600

        img_w, img_h = self.crop_image.size
        # 計算縮放比例
        scale_w = canvas_width / img_w
        scale_h = canvas_height / img_h
        
        # 保持長寬比，留一些邊距 (0.9)
        self.display_scale = min(scale_w, scale_h, 1.0) * 0.9

        new_w = int(img_w * self.display_scale)
        new_h = int(img_h * self.display_scale)

        resized_img = self.crop_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.crop_image_tk = ImageTk.PhotoImage(resized_img)

        # 計算置中偏移
        self.canvas_offset_x = (canvas_width - new_w) // 2
        self.canvas_offset_y = (canvas_height - new_h) // 2

        # 在 Canvas 中心繪製圖片
        is_gif = hasattr(self, '_crop_file_path') and self._crop_file_path.lower().endswith('.gif')
        
        if is_gif:
            # 若動畫未執行或路徑改變則重新啟動
            anim = self._gif_animations.get(self.crop_canvas)
            if not anim or anim.get('path') != self._crop_file_path:
                self._animate_gif_on_canvas(self.crop_canvas, self._crop_file_path, "img_frame")
        else:
            self._stop_animation(self.crop_canvas)
            self.crop_canvas.delete("all")
            self.crop_canvas.create_image(self.canvas_offset_x, self.canvas_offset_y, anchor="nw", image=self.crop_image_tk)
        
        # 初始化裁剪框元件
        # 我們預先建立空的元件，後續只更新座標以提升效能
        self.crop_canvas.create_rectangle(0, 0, 0, 0, outline="#5294e2", width=2, tags=("crop_rect", "crop_box"))
        
        # 建立四個角的控制點
        common_tags = ("crop_rect", "resize_handle")
        self.crop_canvas.create_oval(0, 0, 0, 0, fill="white", outline="#5294e2", tags=common_tags + ("handle_tl",))
        self.crop_canvas.create_oval(0, 0, 0, 0, fill="white", outline="#5294e2", tags=common_tags + ("handle_tr",))
        self.crop_canvas.create_oval(0, 0, 0, 0, fill="white", outline="#5294e2", tags=common_tags + ("handle_bl",))
        self.crop_canvas.create_oval(0, 0, 0, 0, fill="white", outline="#5294e2", tags=common_tags + ("handle_br",))

        # 繪製關閉按鈕（右上角）
        padding = 15
        btn_r = 14
        cx_btn = canvas_width - padding - btn_r
        cy_btn = padding + btn_r
        
        # 為圓形使用特定標籤
        self.crop_canvas.create_oval(cx_btn-btn_r, cy_btn-btn_r, cx_btn+btn_r, cy_btn+btn_r, fill="#eee", outline="#ccc", tags=("crop_rect", "close_btn_bg"))
        self.crop_canvas.create_text(cx_btn, cy_btn, text="✕", fill="#555", font=("Arial", 10, "bold"), tags=("crop_rect", "close_btn_text"))
        
        # 綁定點擊事件至兩者
        self.crop_canvas.tag_bind("close_btn_bg", "<Button-1>", lambda e: self._reset_crop_tab())
        self.crop_canvas.tag_bind("close_btn_text", "<Button-1>", lambda e: self._reset_crop_tab())
        
        # Bind hover to bg
        self.crop_canvas.tag_bind("close_btn_bg", "<Enter>", lambda e: self.crop_canvas.itemconfig("close_btn_bg", fill="#e0e0e0"))
        self.crop_canvas.tag_bind("close_btn_bg", "<Leave>", lambda e: self.crop_canvas.itemconfig("close_btn_bg", fill="#eee"))
        self.crop_canvas.tag_bind("close_btn_text", "<Enter>", lambda e: self.crop_canvas.itemconfig("close_btn_bg", fill="#e0e0e0"))
        self.crop_canvas.tag_bind("close_btn_text", "<Leave>", lambda e: self.crop_canvas.itemconfig("close_btn_bg", fill="#eee"))

        if not hasattr(self, '_gif_animations') or self.crop_canvas not in self._gif_animations:
             self._update_crop_preview()

    def _update_crop_preview(self, event=None):
        if not self.crop_canvas:
            return

        try:
            w = self.crop_vars["width"].get()
            h = self.crop_vars["height"].get()
            x = self.crop_vars["x"].get()
            y = self.crop_vars["y"].get()
        except tk.TclError:
            return # 忽略無效輸入

        # 轉換為 Canvas 座標
        cx = self.canvas_offset_x + (x * self.display_scale)
        cy = self.canvas_offset_y + (y * self.display_scale)
        cw = w * self.display_scale
        ch = h * self.display_scale
        
        if cw < 0: cw = 0
        if ch < 0: ch = 0

        x2 = cx + cw
        y2 = cy + ch

        # 使用 coords 更新座標，避免刪除重建造成的閃爍
        self.crop_canvas.coords("crop_box", cx, cy, x2, y2)
        
        # 更新控制點 (半徑 4)
        r = 4
        self.crop_canvas.coords("handle_tl", cx-r, cy-r, cx+r, cy+r)
        self.crop_canvas.coords("handle_tr", x2-r, cy-r, x2+r, cy+r)
        self.crop_canvas.coords("handle_bl", cx-r, y2-r, cx+r, y2+r)
        self.crop_canvas.coords("handle_br", x2-r, y2-r, x2+r, y2+r)


    def _on_crop_press(self, event):
        # 檢查點擊位置
        x, y = self.crop_canvas.canvasx(event.x), self.crop_canvas.canvasy(event.y)
        self.drag_data["start_x"] = x
        self.drag_data["start_y"] = y
        self.drag_data["mode"] = None

        # 檢查是否點擊到縮放點
        overlap = self.crop_canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item_id in overlap:
            tags = self.crop_canvas.gettags(item_id)
            if "resize_handle" in tags:
                if "handle_tl" in tags: self.drag_data["mode"] = "resize_tl"
                elif "handle_tr" in tags: self.drag_data["mode"] = "resize_tr"
                elif "handle_bl" in tags: self.drag_data["mode"] = "resize_bl"
                elif "handle_br" in tags: self.drag_data["mode"] = "resize_br"
                return

        # 檢查是否點擊到矩形內部 (移動)
        cx = float(self.crop_vars["x"].get()) * self.display_scale + self.canvas_offset_x
        cy = float(self.crop_vars["y"].get()) * self.display_scale + self.canvas_offset_y
        cw = float(self.crop_vars["width"].get()) * self.display_scale
        ch = float(self.crop_vars["height"].get()) * self.display_scale
        
        if cx <= x <= cx + cw and cy <= y <= cy + ch:
             self.drag_data["mode"] = "move"

    def _on_crop_drag(self, event):
        if not self.drag_data["mode"]:
            return

        x, y = self.crop_canvas.canvasx(event.x), self.crop_canvas.canvasy(event.y)
        dx = x - self.drag_data["start_x"]
        dy = y - self.drag_data["start_y"]

        # 將 Canvas 的位移量轉換為圖片像素位移量
        img_dx = int(dx / self.display_scale)
        img_dy = int(dy / self.display_scale)
        
        if img_dx == 0 and img_dy == 0:
            return
            
        cur_x = self.crop_vars["x"].get()
        cur_y = self.crop_vars["y"].get()
        cur_w = self.crop_vars["width"].get()
        cur_h = self.crop_vars["height"].get()

        if self.drag_data["mode"] == "move":
            new_x = cur_x + img_dx
            new_y = cur_y + img_dy
            
            # 限制邊界
            img_w, img_h = self.crop_image.size
            if new_x < 0: new_x = 0
            if new_y < 0: new_y = 0
            if new_x + cur_w > img_w: new_x = img_w - cur_w
            if new_y + cur_h > img_h: new_y = img_h - cur_h

            self.crop_vars["x"].set(new_x)
            self.crop_vars["y"].set(new_y)
            
        elif self.drag_data["mode"].startswith("resize"):
            mode = self.drag_data["mode"]
            min_size = 10
            
            new_x, new_y, new_w, new_h = cur_x, cur_y, cur_w, cur_h
            
            # 處理 Y 軸變化
            if "t" in mode: # Top
                # 向上拖動 dy 為負 -> 高度增加, y 減少
                # 向下拖動 dy 為正 -> 高度減少, y 增加
                # 防止高度過小
                if cur_h - img_dy < min_size:
                    img_dy = cur_h - min_size # 修正 dy 為最大允許值
                
                new_y = cur_y + img_dy
                new_h = cur_h - img_dy
            elif "b" in mode: # Bottom
                # 向下拖動 dy 為正 -> 高度增加
                if cur_h + img_dy < min_size:
                     img_dy = min_size - cur_h # 修正 dy 
                     
                new_h = cur_h + img_dy

            # 處理 X 軸變化
            if "l" in mode: # Left
                if cur_w - img_dx < min_size:
                    img_dx = cur_w - min_size
                
                new_x = cur_x + img_dx
                new_w = cur_w - img_dx
            elif "r" in mode: # Right
                if cur_w + img_dx < min_size:
                    img_dx = min_size - cur_w
                
                new_w = cur_w + img_dx

            self.crop_vars["x"].set(new_x)
            self.crop_vars["y"].set(new_y)
            self.crop_vars["width"].set(new_w)
            self.crop_vars["height"].set(new_h)

        # 更新起始點
        self.drag_data["start_x"] = x
        self.drag_data["start_y"] = y
        
        self._update_crop_preview()

    def _on_crop_release(self, event):
        self.drag_data["mode"] = None



    # --- 調整大小分頁功能 ---
    def _create_resize_tab_content(self, parent):
        center_frame = ttk.Frame(parent)
        center_frame.place(relx=0.5, rely=0.4, anchor="center")

        title_label = ttk.Label(center_frame, text="調整圖片的大小", font=(self.font_family, 24, "bold"))
        title_label.pack(pady=(0, 15))

        desc_text = "以像素或百分比定義尺寸。\n縮放 JPG, PNG, GIF 文檔。"
        desc_label = ttk.Label(center_frame, text=desc_text, justify="center", font=(self.font_family, 11))
        desc_label.pack(pady=(0, 30))

        btn_frame = ttk.Frame(center_frame)
        btn_frame.pack()
        
        select_btn = ttk.Button(btn_frame, text="選擇多張圖片", style="Large.TButton", command=self._select_resize_images)
        select_btn.pack(side="left", padx=5)

        bottom_label = ttk.Label(center_frame, text="或者將多張圖片拖動到這裏", font=(self.font_family, 9), foreground="gray")
        bottom_label.pack(pady=(15, 0))

    def _select_resize_images(self):
        files = filedialog.askopenfilenames(title="選擇圖片", filetypes=[("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.webp *.gif")])
        if files:
            # 這裡我們只取第一張圖片進行編輯
            self._resize_file_path = files[0] # 保存原始路徑
            self._load_resize_image_on_canvas(files[0])
            self._switch_to_resize_editor()

    def _switch_to_resize_editor(self):
        for widget in self.resize_tab.winfo_children():
            widget.destroy()
        self._create_resize_editor_ui(self.resize_tab)

    def _create_resize_editor_ui(self, parent):
        paned = ttk.PanedWindow(parent, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 左側畫布
        self.resize_canvas = tk.Canvas(paned, bg='#cccccc') # 較深的灰色以最大化對比度/檢查置中
        paned.add(self.resize_canvas, weight=1)

        # 右側設定
        settings_frame = ttk.Frame(paned, padding="5") # 減少填充
        paned.add(settings_frame, weight=0)

        # 標題較小
        ttk.Label(settings_frame, text="調整尺寸的選項", font=(self.font_family, 14, "bold"), anchor="center").pack(pady=(0, 15), fill=tk.X)

        # 模式選擇（自訂切換）
        self.resize_mode_var = tk.StringVar(value="pixels") 
        
        mode_frame = ttk.Frame(settings_frame)
        mode_frame.pack(fill=tk.X, pady=(0, 0))
        
        # 使用 Canvas 模擬自定義按鈕 - 明確寬度以保持面板精簡
        self.btn_pixel_canvas = tk.Canvas(mode_frame, width=100, height=70, bg="white", highlightthickness=1, highlightbackground="#ccc")
        self.btn_pixel_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_pixel_canvas.bind("<Button-1>", lambda e: self._set_resize_mode("pixels"))
        
        self.btn_percent_canvas = tk.Canvas(mode_frame, width=100, height=70, bg="#f9f9f9", highlightthickness=1, highlightbackground="#ccc")
        self.btn_percent_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.btn_percent_canvas.bind("<Button-1>", lambda e: self._set_resize_mode("percentage"))
        
        # 繪製按鈕內容
        self._draw_mode_button(self.btn_pixel_canvas, "按像素", True) # 初始選中
        self._draw_mode_button(self.btn_percent_canvas, "按百分比", False)

        ttk.Separator(settings_frame, orient='horizontal').pack(fill='x', pady=10)

        # -- 像素輸入區域 --
        self.pixels_frame = ttk.Frame(settings_frame)
        
        ttk.Label(self.pixels_frame, text="將所有圖片的尺寸調整為:", font=self.font_normal, foreground="#555").pack(anchor="w", pady=(0, 10))

        # 寬度
        w_frame = ttk.Frame(self.pixels_frame)
        w_frame.pack(fill=tk.X, pady=2)
        ttk.Label(w_frame, text="寬度 (px):", font=self.font_bold).pack(side=tk.LEFT)
        self.resize_w_var = tk.IntVar()
        self.spin_w = ttk.Spinbox(w_frame, from_=1, to=1000000, textvariable=self.resize_w_var, font=self.font_normal, width=8) # Smaller width
        self.spin_w.pack(side=tk.RIGHT)
        self.spin_w.bind("<KeyRelease>", lambda e: self._on_resize_dim_change('w'))
        
        # 高度
        h_frame = ttk.Frame(self.pixels_frame)
        h_frame.pack(fill=tk.X, pady=10)
        ttk.Label(h_frame, text="高度 (px):", font=self.font_bold).pack(side=tk.LEFT)
        self.resize_h_var = tk.IntVar()
        self.spin_h = ttk.Spinbox(h_frame, from_=1, to=1000000, textvariable=self.resize_h_var, font=self.font_normal, width=8) # Smaller width
        self.spin_h.pack(side=tk.RIGHT)
        self.spin_h.bind("<KeyRelease>", lambda e: self._on_resize_dim_change('h'))

        
        ttk.Separator(self.pixels_frame, orient='horizontal').pack(fill='x', pady=10)

        # 選項
        self.maintain_aspect_var = tk.BooleanVar(value=False)
        self.no_enlarge_var = tk.BooleanVar(value=False)
        
        
        # -- Percentage Inputs Area --
        self.percent_frame = ttk.Frame(settings_frame)
        self.resize_percent_var = tk.IntVar(value=50) # Default
        
        # 建立選項列表
        self._percent_options_frame = ttk.Frame(self.percent_frame)
        self._percent_options_frame.pack(fill=tk.X)
        
        self._draw_percent_option(25, "縮小 25%")
        self._draw_percent_option(50, "縮小 50%")
        self._draw_percent_option(75, "縮小 75%")
        
        # 動作按鈕（底部）
        self.btn_action_canvas = tk.Canvas(settings_frame, height=45, bg="#4285f4", highlightthickness=0, cursor="hand2") # 稍微較小的高度
        self.btn_action_canvas.pack(side=tk.BOTTOM, fill=tk.X, pady=15)
        # 繪製文字與箭頭
        self.btn_text_id = self.btn_action_canvas.create_text(50, 22.5, text="下載圖片", fill="black", font=(self.font_family, 11, "bold"), anchor="center") # 較短的文字
        self.btn_action_canvas.bind("<Button-1>", lambda e: self._perform_resize_and_save())
        self.btn_action_canvas.bind("<Configure>", self._center_action_btn_text)


        # 初始狀態
        if self.resize_image:
             self.resize_w_var.set(self.resize_image.width)
             self.resize_h_var.set(self.resize_image.height)
             
        self._update_resize_ui_state()
        # 綁定 configure 事件以確保動態調整大小/置中
        self.resize_canvas.bind("<Configure>", self._draw_resize_canvas_content)

    def _center_action_btn_text(self, event):
        w, h = event.width, event.height
        self.btn_action_canvas.coords(self.btn_text_id, w/2, h/2)

    def _draw_mode_button(self, canvas, text, is_selected):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w <= 1: w = 100 # Reduced default guess
        h = 70 # Reduced height
        
        bg = "white" if is_selected else "#f9f9f9"
        canvas.configure(bg=bg)
        
        # Icon placeholder (Grid dots)
        if "像素" in text:
            # Draw simple grid icon
            off_x = w/2 - 12
            off_y = 15
            canvas.create_rectangle(off_x, off_y, off_x+10, off_y+10, fill="#333")
            canvas.create_rectangle(off_x+12, off_y, off_x+22, off_y+10, fill="#333")
            canvas.create_rectangle(off_x, off_y+12, off_x+10, off_y+22, fill="#333")
            canvas.create_rectangle(off_x+12, off_y+12, off_x+22, off_y+22, fill="#bbb") 
        else:
            # Draw percent icon
             off_x = w/2 - 12
             off_y = 15
             canvas.create_rectangle(off_x, off_y, off_x+25, off_y+25, outline="#333", width=2)
             canvas.create_text(off_x+12, off_y+12, text="%", font=("Arial", 10, "bold"))
        
        canvas.create_text(w/2, 55, text=text, fill="black", font=(self.font_family, 9))
        
        if is_selected:
            # Green Checkmark circle at top left
            canvas.create_oval(8, 8, 22, 22, fill="#25d366", outline="")
            canvas.create_text(15, 15, text="✓", fill="white", font=("Arial", 9, "bold"))

    def _set_resize_mode(self, mode):
        self.resize_mode_var.set(mode)
        is_pixel = (mode == "pixels")
        self._draw_mode_button(self.btn_pixel_canvas, "按像素", is_pixel)
        self._draw_mode_button(self.btn_percent_canvas, "按百分比", not is_pixel)
        self._update_resize_ui_state()

    def _draw_percent_option(self, value, text):
        # 為每個選項建立可點擊的框架
        frame = tk.Canvas(self._percent_options_frame, height=50, bg="white", highlightthickness=0)
        frame.pack(fill=tk.X, pady=1)
        frame.value = value
        
        # 儲存畫布引用以便稍後更新
        if not hasattr(self, "_percent_canvases"): self._percent_canvases = {}
        self._percent_canvases[value] = frame
        
        frame.bind("<Button-1>", lambda e, v=value: self._set_percent_choice(v))
        
        # 初始繪製
        self._redraw_percent_option(frame, text, value == self.resize_percent_var.get())

    def _redraw_percent_option(self, canvas, text, is_selected):
        canvas.delete("all")
        w = canvas.winfo_width()
        if w <= 1: w = 300
        h = 50
        
        bg = "#e8f0fe" if is_selected else "white"
        text_color = "black"
        canvas.configure(bg=bg)
        
        canvas.create_text(20, h/2, text=text, fill=text_color, anchor="w", font=(self.font_family, 11))
        
        if is_selected:
            # Green check circle on right
            cx = w - 30
            cy = h/2
            canvas.create_oval(cx-10, cy-10, cx+10, cy+10, fill="#25d366", outline="")
            canvas.create_text(cx, cy, text="✓", fill="white", font=("Arial", 10, "bold"))
            
        # Border bottom
        canvas.create_line(0, h-1, w, h-1, fill="#eee")

    def _set_percent_choice(self, value):
        self.resize_percent_var.set(value)
        # 重繪所有選項
        for v, canvas in self._percent_canvases.items():
            text = f"縮小 {v}%"
            self._redraw_percent_option(canvas, text, v == value)
        self._draw_info_overlay()

    def _update_resize_ui_state(self):
        mode = self.resize_mode_var.get()
        if mode == "pixels":
            self.percent_frame.pack_forget()
            self.pixels_frame.pack(fill=tk.X, pady=10)
        else:
            self.pixels_frame.pack_forget()
            self.percent_frame.pack(fill=tk.X, pady=10)
        self._draw_info_overlay()

    def _on_resize_dim_change(self, source):
        if not self.maintain_aspect_var.get() or not self.resize_image:
            self._draw_info_overlay()
            return
            
        try:
            w = self.resize_w_var.get()
            h = self.resize_h_var.get()
            img_w, img_h = self.resize_image.size
            aspect = img_w / img_h
            
            if source == 'w':
                # Width changed, update height
                new_h = int(w / aspect)
                self.resize_h_var.set(new_h)
            elif source == 'h':
                # Height changed, update width
                new_w = int(h * aspect)
                self.resize_w_var.set(new_w)
        except tk.TclError:
            pass
        self._draw_info_overlay()

    def _load_resize_image_on_canvas(self, file_path):
        if hasattr(self, 'resize_canvas'):
            self._stop_animation(self.resize_canvas)
        self.resize_image = Image.open(file_path)

    def _draw_resize_canvas_content(self, event=None):
        if not self.resize_image:
            return
        
        # 不強制更新，若可用則使用事件寬度/高度
        if event:
            cw = event.width
            ch = event.height
        else:
            self.resize_canvas.update_idletasks()
            cw = self.resize_canvas.winfo_width()
            ch = self.resize_canvas.winfo_height()
            
        if cw <= 1: cw = 800
        if ch <= 1: ch = 600
        
        img_w, img_h = self.resize_image.size
        # 適應邏輯
        scale = min(cw/img_w, ch/img_h, 1.0) * 0.9
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        resized = self.resize_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.resize_image_tk = ImageTk.PhotoImage(resized)
        
        off_x = (cw - new_w) // 2
        off_y = (ch - new_h) // 2
        
        # 若為 GIF，則讓動畫處理器處理圖片部分
        is_gif = hasattr(self, '_resize_file_path') and self._resize_file_path.lower().endswith('.gif')
        
        if is_gif:
            anim = self._gif_animations.get(self.resize_canvas)
            if not anim or anim.get('path') != self._resize_file_path:
                self._animate_gif_on_canvas(self.resize_canvas, self._resize_file_path, "img_frame")
        else:
            self._stop_animation(self.resize_canvas)
            self.resize_canvas.delete("all")
            self.resize_canvas.create_image(off_x, off_y, anchor="nw", image=self.resize_image_tk)
        
        # Draw the info overlay
        self._draw_info_overlay()

    def _draw_info_overlay(self):
        self.resize_canvas.delete("overlay")
        if not self.resize_image: return

        # Calculate Dimensions
        orig_w, orig_h = self.resize_image.size
        
        target_w, target_h = 0, 0
        mode = self.resize_mode_var.get()
        if mode == "pixels":
            try:
                target_w = self.resize_w_var.get()
                target_h = self.resize_h_var.get()
                if self.no_enlarge_var.get():
                     if target_w > orig_w: target_w = orig_w
                     # If maintaining aspect, recalc H? Or just let it be?
                     # Simple logic: cap values. 
                     if target_h > orig_h: target_h = orig_h # Simplified cap
            except:
                pass
        else:
            p = self.resize_percent_var.get()
            target_w = int(orig_w * p / 100)
            target_h = int(orig_h * p / 100)

        # 繪製疊加層
        cw = self.resize_canvas.winfo_width()
        ch = self.resize_canvas.winfo_height()
        cx = cw / 2
        cy = ch - 60 # Position from bottom
        
        fname = os.path.basename(self._resize_file_path) if hasattr(self, "_resize_file_path") else "Image"
        
        # Draw Filename
        self.resize_canvas.create_text(cx, cy - 30, text=fname, fill="#555", font=(self.font_family, 10), tags="overlay")
        
        # Draw Pills
        def draw_pill(x, y, text, bg, fg):
            # 根據文字長度計算大約寬度
            w = len(text) * 8 + 20
            h = 24
            x1 = x - w/2
            y1 = y - h/2
            x2 = x + w/2
            y2 = y + h/2
            
            # Draw rounded rect (using overlapping oval/rect)
            r = 12
            self.resize_canvas.create_oval(x1, y1, x1+2*r, y1+2*r, fill=bg, outline=bg, tags="overlay")
            self.resize_canvas.create_oval(x2-2*r, y2-2*r, x2, y2, fill=bg, outline=bg, tags="overlay")
            self.resize_canvas.create_rectangle(x1+r, y1, x2-r, y2, fill=bg, outline=bg, tags="overlay")
            self.resize_canvas.create_rectangle(x1, y1+r, x2, y2-r, fill=bg, outline=bg, tags="overlay")
            
            # 文字
            self.resize_canvas.create_text(x, y, text=text, fill=fg, font=("Arial", 9, "bold"), tags="overlay")

        # 原始
        orig_txt = f"{orig_w} x {orig_h}"
        draw_pill(cx - 70, cy, orig_txt, "#999", "white")
        
        # Arrow
        self.resize_canvas.create_text(cx, cy, text="➔", fill="#555", font=("Arial", 12, "bold"), tags="overlay")
        
        # Target
        target_txt = f"{target_w} x {target_h}"
        draw_pill(cx + 70, cy, target_txt, "#4285f4", "white")

        # 繪製關閉按鈕（右上角）
        padding = 15
        btn_r = 14
        cx_btn = cw - padding - btn_r
        cy_btn = padding + btn_r
        
        # 為圓形使用特定標籤
        self.resize_canvas.create_oval(cx_btn-btn_r, cy_btn-btn_r, cx_btn+btn_r, cy_btn+btn_r, fill="#eee", outline="#ccc", tags=("overlay", "close_btn_bg"))
        self.resize_canvas.create_text(cx_btn, cy_btn, text="✕", fill="#555", font=("Arial", 10, "bold"), tags=("overlay", "close_btn_text"))
        
        # 綁定點擊事件至兩者
        self.resize_canvas.tag_bind("close_btn_bg", "<Button-1>", lambda e: self._reset_resize_tab())
        self.resize_canvas.tag_bind("close_btn_text", "<Button-1>", lambda e: self._reset_resize_tab())
        
        # 綁定懸停事件至背景
        self.resize_canvas.tag_bind("close_btn_bg", "<Enter>", lambda e: self.resize_canvas.itemconfig("close_btn_bg", fill="#e0e0e0"))
        self.resize_canvas.tag_bind("close_btn_bg", "<Leave>", lambda e: self.resize_canvas.itemconfig("close_btn_bg", fill="#eee"))
        self.resize_canvas.tag_bind("close_btn_text", "<Enter>", lambda e: self.resize_canvas.itemconfig("close_btn_bg", fill="#e0e0e0"))
        self.resize_canvas.tag_bind("close_btn_text", "<Leave>", lambda e: self.resize_canvas.itemconfig("close_btn_bg", fill="#eee"))

    def _perform_resize_and_save(self):
        if not self.resize_image: return
        
        mode = self.resize_mode_var.get()
        
        try:
            if mode == "pixels":
                target_w = self.resize_w_var.get()
                target_h = self.resize_h_var.get()
                
                # Check "Do not enlarge"
                if self.no_enlarge_var.get():
                     orig_w, orig_h = self.resize_image.size
                     if target_w > orig_w or target_h > orig_h:
                         # 還原為原始？還是僅限制？
                         # 若需要，將限制為原始尺寸並維持長寬比
                         # 簡單邏輯：若目標寬度 > 原始寬度，使用原始寬度
                         if target_w > orig_w:
                             target_w = orig_w
                             target_h = int(orig_w / (self.resize_image.width / self.resize_image.height))
            
            else: # percentage
                percent = self.resize_percent_var.get()
                orig_w, orig_h = self.resize_image.size
                target_w = int(orig_w * percent / 100)
                target_h = int(orig_h * percent / 100)
                
        except:
             messagebox.showerror("錯誤", "無效的尺寸")
             return

        if target_w <= 0 or target_h <= 0:
             messagebox.showerror("錯誤", "尺寸必須大於 0")
             return

        try:
            resized = self.resize_image.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            file_path = filedialog.asksaveasfilename(
                title="儲存圖片",
                defaultextension=".jpg",
                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png"), ("GIF", "*.gif"), ("All Files", "*.*")]
            )
            
            if file_path:
                if file_path.lower().endswith('.gif'):
                     # 儲存為動態 GIF
                    frames = []
                    duration = self.resize_image.info.get('duration', 100)
                    try:
                        for frame in ImageSequence.Iterator(self.resize_image):
                            f = frame.copy().convert('RGBA')
                            f = f.resize((target_w, target_h), Image.Resampling.LANCZOS)
                            frames.append(f)
                        
                        if frames:
                            frames[0].save(file_path, save_all=True, append_images=frames[1:], loop=0, duration=duration, optimize=False, disposal=2)
                        else:
                            resized.save(file_path)
                    except Exception as e:
                        print(f"GIF save error: {e}")
                        resized.save(file_path)
                else:
                    resized.save(file_path)

                messagebox.showinfo("成功", f"圖片已儲存至:\n{file_path}")
                self._reset_resize_tab()
        except Exception as e:
            messagebox.showerror("錯誤", f"失敗:\n{e}")


    def _reset_resize_tab(self):
        if hasattr(self, 'resize_canvas'):
            self._stop_animation(self.resize_canvas)
        for widget in self.resize_tab.winfo_children():
            widget.destroy()
        self.resize_image = None
        self._create_resize_tab_content(self.resize_tab)


    def _create_convert_tab_content(self, parent):
        # 原本的 main_frame 邏輯現在移到這裡
        main_frame = ttk.Frame(parent, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=1)

        left_panel = ttk.Frame(main_frame, padding="10")
        left_panel.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        left_panel.grid_rowconfigure(1, weight=0)

        right_panel = ttk.Frame(main_frame, padding="10")
        right_panel.grid(row=0, column=1, sticky="nsew")
        right_panel.grid_rowconfigure(0, weight=1)
        right_panel.grid_columnconfigure(0, weight=1)

        # --- 建立元件 ---
        self._create_input_widgets(left_panel)
        self._create_settings_widgets(left_panel)
        self._create_action_widgets(left_panel)

        self._create_file_list_widgets(right_panel)
        self._create_status_widgets(right_panel)
        
        
    # --- 壓縮功能 (三階段流程) ---
    def _create_compress_tab_content(self, parent):
        self.compress_container = ttk.Frame(parent)
        self.compress_container.pack(fill=tk.BOTH, expand=True)
        self.compress_files_list = []
        self._show_compress_landing()

    def _show_compress_landing(self):
        for widget in self.compress_container.winfo_children():
            widget.destroy()

        center_frame = ttk.Frame(self.compress_container)
        center_frame.place(relx=0.5, rely=0.4, anchor="center")

        title_label = ttk.Label(center_frame, text="壓縮圖片文檔", font=(self.font_family, 24, "bold"), foreground="#666")
        title_label.pack(pady=(0, 15))

        desc_text = "壓縮 JPG, PNG或GIF，並保持最佳質量。\n批量縮小多個圖片的尺寸。"
        desc_label = ttk.Label(center_frame, text=desc_text, justify="center", font=(self.font_family, 11), foreground="#555")
        desc_label.pack(pady=(0, 30))

        btn_frame = ttk.Frame(center_frame)
        btn_frame.pack()
        
        # 使用 ttk.Button 取代之前自訂的 Canvas 以維持一致性 (匹配第三張截圖)
        select_btn = ttk.Button(btn_frame, text="選擇多張圖片", style="Large.TButton", command=self._select_compress_images)
        select_btn.pack()

        bottom_label = ttk.Label(center_frame, text="或者將多張圖片拖動到這裏", font=(self.font_family, 9), foreground="gray")
        bottom_label.pack(pady=(15, 0))

    def _select_compress_images(self):
        files = filedialog.askopenfilenames(
            title="選擇要壓縮的圖片", 
            filetypes=[("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.gif")]
        )
        if files:
            self.compress_files_list = list(files)
            self._show_compress_review()

    def _show_compress_review(self):
        for widget in self.compress_container.winfo_children():
            widget.destroy()

        # Header
        header_frame = ttk.Frame(self.compress_container, padding="20")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="壓縮多個圖片", font=(self.font_family, 18, "bold"), foreground="#333").pack(anchor="center")

        # Main Content Area (Split Left/Right)
        content_frame = ttk.Frame(self.compress_container, padding="20")
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left Panel (Scrollable File List) - Weight 3
        left_panel = ttk.Frame(content_frame)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        canvas = tk.Canvas(left_panel, bg="#f5f7fa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        # Center the frame: anchor="n" (North/Top-Center)
        # We start at (0,0) but will update on configure
        self.compress_window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="n")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Update window position on canvas resize to keep it centered
        def on_canvas_configure(event):
            # Update scrollregion
            canvas.configure(scrollregion=canvas.bbox("all"))
            # Center the window by moving it to (width/2, 0)
            # We do NOT set the width of the frame, letting it shrink to fit content
            canvas.coords(self.compress_window_id, event.width // 2, 0)

        canvas.bind("<Configure>", on_canvas_configure)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Vertical Separator
        separator = ttk.Frame(content_frame, width=2, style="Separator.TFrame") # Or just a colored frame
        separator_canvas = tk.Canvas(content_frame, width=2, bg="white", highlightthickness=0) # Distinct white separator gap
        separator_canvas.pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Right Panel (Actions) - Weight 1
        right_panel = ttk.Frame(content_frame, width=300) # Fixed width for actions
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False) # Enforce width

        # Populate File List (Cards)
        self._thumbnail_cache = [] # Reset cache
        
        # Grid layout for cards (e.g., 3 columns)
        row = 0
        col = 0
        max_cols = 3 
        
        for i, file_path in enumerate(self.compress_files_list):
            self._create_thumbnail_card(scrollable_frame, file_path, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Right Panel Content
        # Info Box
        info_box = tk.Label(right_panel, text="所有圖片都將被壓縮，同時保持最佳品質和大小比例。", 
                            bg="#dbeafe", fg="#333", font=(self.font_family, 11), pady=20, padx=20, wraplength=260, justify="left")
        info_box.pack(fill=tk.X, pady=(0, 40))

        # Start Button
        self.btn_compress_action = tk.Canvas(right_panel, width=280, height=60, bg="#f0f0f0", highlightthickness=0, cursor="hand2")
        self.btn_compress_action.pack(pady=20)
        
        def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
            points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
            return canvas.create_polygon(points, **kwargs, smooth=True)

        round_rectangle(self.btn_compress_action, 2, 2, 278, 58, radius=20, fill="#4285f4", outline="")
        self.btn_compress_action.create_text(140, 30, text="壓縮多個圖片文檔 ➔", fill="black", font=(self.font_family, 13, "bold"))
        self.btn_compress_action.bind("<Button-1>", lambda e: self._initiate_compression())

    def _create_thumbnail_card(self, parent, file_path, row, col):
        card_frame = tk.Frame(parent, bg="white", padx=5, pady=5) # Simple card
        # Border
        card_frame.grid(row=row, column=col, padx=10, pady=10)
        
        # Shadow/Border effect wrapper
        border = tk.Frame(parent, bg="#ddd", padx=1, pady=1)
        border.grid(row=row, column=col, padx=10, pady=10)
        
        card = tk.Frame(border, bg="white", width=150, height=180)
        card.pack()
        card.pack_propagate(False)
        
        # Remove Button (Top-Right)
        # Using a canvas for absolute positioning relative to card
        remove_btn = tk.Canvas(card, width=20, height=20, bg="white", highlightthickness=0, cursor="hand2")
        remove_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-2, y=2)
        remove_btn.create_oval(2, 2, 18, 18, fill="#eee", outline="#ccc")
        remove_btn.create_text(10, 10, text="✕", fill="#666", font=("Arial", 9))
        remove_btn.bind("<Button-1>", lambda e, p=file_path: self._remove_compress_file(p))

        try:
            # Thumbnail
            img = Image.open(file_path)
            img.thumbnail((120, 120))
            photo = ImageTk.PhotoImage(img)
            self._thumbnail_cache.append(photo) # Keep ref
            
            img_label = tk.Label(card, image=photo, bg="white")
            img_label.pack(pady=(25, 5)) # Space for X button
            
            # Start animation if GIF
            if file_path.lower().endswith('.gif'):
                self._animate_gif(img_label, file_path)
            
            # Filename
            fname = os.path.basename(file_path)
            if len(fname) > 15: fname = fname[:12] + "..."
            tk.Label(card, text=fname, bg="white", fg="#555", font=(self.font_family, 9)).pack()
            
        except Exception:
            tk.Label(card, text="無法預覽", bg="white").pack(pady=40)

    def _remove_compress_file(self, file_path):
        if file_path in self.compress_files_list:
            self.compress_files_list.remove(file_path)
            if not self.compress_files_list:
                self._show_compress_landing()
            else:
                self._show_compress_review() # Refresh

    def _initiate_compression(self):
        output_dir = filedialog.askdirectory(title="選擇輸出資料夾")
        if not output_dir:
            return
        
        self._perform_batch_compression(output_dir)

    def _perform_batch_compression(self, output_dir):
        # 初始化統計數據
        self.compression_stats = {"total_orig": 0, "total_new": 0, "count": 0}
        self.last_output_dir = output_dir
        
        # 建立進度視窗或隱藏當前介面以顯示處理中 (可選)
        
        # 循環處理每個檔案
        for file_path in self.compress_files_list:
            try:
                # 這裡原本是手動處理，現在改用 ImageProcessor 類別
                # 為了獲取大小，我們調用 _convert_and_save
                # 注意：compression 通常不需要 resize，所以 resize_options=None
                result = self.processor._convert_and_save(
                    file_path, 
                    output_dir, 
                    output_format=os.path.splitext(file_path)[1][1:].upper() or "JPEG",
                    quality=75, # 預設壓縮品質
                    resize_options=None
                )
                
                self.compression_stats["total_orig"] += result["original_size"]
                self.compression_stats["total_new"] += result["compressed_size"]
                self.compression_stats["count"] += 1
                
                # 防止 UI 凍結
                self.update()
                    
            except Exception as e:
                print(f"壓縮過程中出錯: {e}")
        
        # 處理完成後顯示結果頁面
        if self.compression_stats["count"] > 0:
            self._show_compress_result()
        else:
            messagebox.showwarning("提示", "沒有圖片被成功壓縮。")
            self._show_compress_landing()

    def _show_compress_result(self):
        for widget in self.compress_container.winfo_children():
            widget.destroy()

        content = ttk.Frame(self.compress_container)
        content.place(relx=0.5, rely=0.45, anchor="center")

        # Title
        ttk.Label(content, text="你的圖片已被壓縮!", font=(self.font_family, 24, "bold"), foreground="#333").pack(pady=(0, 30))

        # Download Button Row
        row1 = ttk.Frame(content)
        row1.pack(pady=20)
        
        # Back Arrow
        arrow_canvas = tk.Canvas(row1, width=40, height=40, bg="#f0f0f0", highlightthickness=0, cursor="hand2")
        arrow_canvas.pack(side=tk.LEFT, padx=(0, 15))
        arrow_canvas.create_oval(2, 2, 38, 38, fill="#444")
        arrow_canvas.create_text(20, 20, text="←", fill="black", font=("Arial", 16, "bold"))
        arrow_canvas.bind("<Button-1>", lambda e: self._show_compress_landing())

        # Blue Button
        dl_btn = tk.Canvas(row1, width=350, height=60, bg="#f0f0f0", highlightthickness=0, cursor="hand2")
        dl_btn.pack(side=tk.LEFT)
        
        # Round Rect helper again
        def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
            points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
            return canvas.create_polygon(points, **kwargs, smooth=True)

        round_rectangle(dl_btn, 2, 2, 348, 58, radius=10, fill="#4285f4", outline="")
        
        # Draw tray icon
        cx, cy = 90, 30 # Icon center
        dl_btn.create_line(cx, cy-10, cx, cy+5, fill="white", width=3, capstyle="round") # Shaft
        dl_btn.create_line(cx-7, cy-2, cx, cy+5, cx+7, cy-2, fill="white", width=3, capstyle="round", joinstyle="round") # Arrow head
        dl_btn.create_line(cx-10, cy+5, cx-10, cy+12, cx+10, cy+12, cx+10, cy+5, fill="white", width=3, capstyle="round") # Tray
        
        dl_btn.create_text(210, 30, text="下載已壓縮的圖片文檔", fill="black", font=(self.font_family, 14, "bold"))
        dl_btn.bind("<Button-1>", lambda e: os.startfile(self.last_output_dir) if os.name == 'nt' else None)

        # Stats Area
        stats_frame = ttk.Frame(content)
        stats_frame.pack(pady=40)
        
        # Calc savings
        orig = self.compression_stats.get("total_orig", 1)
        new = self.compression_stats.get("total_new", 1)
        saved_percent = max(0, int((1 - new/orig) * 100))
        
        # Circular Progress
        prog_canvas = tk.Canvas(stats_frame, width=100, height=100, bg="#f0f0f0", highlightthickness=0)
        prog_canvas.pack(side=tk.LEFT, padx=20)
        
        # Background circle
        prog_canvas.create_oval(10, 10, 90, 90, outline="#ddd", width=8)
        # Arc
        # extent = 3.6 * saved_percent (full circle 360)
        extent = 3.6 * saved_percent
        if extent < 10: extent = 10 # Min visible
        prog_canvas.create_arc(10, 10, 90, 90, start=90, extent=-extent, style="arc", outline="#4285f4", width=8)
        
        prog_canvas.create_text(50, 40, text=f"{saved_percent}%", font=(self.font_family, 16, "bold"), fill="#4285f4") # 改為藍色
        prog_canvas.create_text(50, 65, text="已減小", font=(self.font_family, 9), fill="#666") # 改為「已減小」更貼切

        # Text Stats
        txt_frame = ttk.Frame(stats_frame)
        txt_frame.pack(side=tk.LEFT)
        
        ttk.Label(txt_frame, text=f"你的圖片 減小了{saved_percent}% !", font=(self.font_family, 14), foreground="#333").pack(anchor="w")
        
        def fmt_size(b):
            if b < 1024: return f"{b} B"
            if b < 1024*1024: return f"{b/1024:.2f} KB"
            return f"{b/(1024*1024):.2f} MB"
            
        sz_text = f"{fmt_size(orig)} -> {fmt_size(new)}"
        ttk.Label(txt_frame, text=sz_text, font=(self.font_family, 12, "bold"), foreground="#666").pack(anchor="w", pady=(5, 0))

    def _create_input_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="1. 選擇來源", padding="15")
        frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        frame.grid_columnconfigure(0, weight=1)
        btn_files = ttk.Button(frame, text="📂 選擇圖片檔案", command=self._select_files, style="Blue.TButton")
        btn_files.grid(row=0, column=0, sticky="ew", pady=5)

    def _create_settings_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="2. 進行設定", padding="15")
        frame.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        frame.grid_columnconfigure(1, weight=1)

        ttk.Label(frame, text="輸出格式:").grid(row=0, column=0, sticky="w", pady=5)
        self.output_format_var = tk.StringVar(value="JPEG")
        formats = ["JPEG", "PNG", "BMP", "WEBP", "GIF"]
        format_menu = ttk.OptionMenu(frame, self.output_format_var, formats[0], *formats, command=self._on_format_change)
        format_menu.grid(row=0, column=1, sticky="ew", pady=5)

        self.quality_frame = ttk.Frame(frame)
        self.quality_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)
        ttk.Label(self.quality_frame, text="品質 (JPEG):").grid(row=0, column=0, sticky="w")
        self.quality_var = tk.IntVar(value=95)

        # Custom Quality Slider
        self.quality_enabled = True
        self.quality_slider_canvas = tk.Canvas(self.quality_frame, height=20, width=50, bg=self.style.lookup("TFrame", "background"), highlightthickness=0, cursor="hand2")
        self.quality_slider_canvas.grid(row=0, column=1, sticky="ew", padx=10)
        
        self.quality_slider_canvas.bind("<Button-1>", self._on_quality_slider_interact)
        self.quality_slider_canvas.bind("<B1-Motion>", self._on_quality_slider_interact)
        self.quality_slider_canvas.bind("<Configure>", lambda e: self._draw_quality_slider())
        self.quality_label = ttk.Label(self.quality_frame, text="95%", font=self.font_normal)
        self.quality_label.grid(row=0, column=2)

    def _draw_quality_slider(self):
        cv = self.quality_slider_canvas
        if not cv.winfo_exists(): return
        
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w <= 1: return
        
        cv.delete("all")
        
        # Calculate positions
        current = self.quality_var.get()
        # Scale 1-100
        ratio = (current - 1) / 99.0
        ratio = max(0, min(1, ratio))
        
        margin_x = 10
        track_w = w - 2 * margin_x
        cy = h / 2
        
        thumb_x = margin_x + track_w * ratio
        
        # Colors
        bg_color = "#e0e0e0"
        fill_color = "#4285f4" if self.quality_enabled else "#b0b0b0"
        thumb_outline = "#4285f4" if self.quality_enabled else "#b0b0b0"
        
        # Draw Background Track (Gray)
        cv.create_line(margin_x, cy, w - margin_x, cy, fill=bg_color, width=4, capstyle="round")
        
        # Draw Progress Track
        if self.quality_enabled and ratio > 0:
            cv.create_line(margin_x, cy, thumb_x, cy, fill=fill_color, width=4, capstyle="round")
            
        # Draw Thumb (Circle)
        r = 5
        cv.create_oval(thumb_x - r, cy - r, thumb_x + r, cy + r, fill="white", outline=thumb_outline, width=2)
        
    def _on_quality_slider_interact(self, event):
        if not self.quality_enabled: return
        
        cv = self.quality_slider_canvas
        w = cv.winfo_width()
        margin_x = 10
        track_w = w - 2 * margin_x
        
        x = event.x - margin_x
        ratio = max(0, min(1, x / track_w))
        
        # Map ratio to 1-100
        new_val = 1 + int(ratio * 99)
        
        if new_val != self.quality_var.get():
            self.quality_var.set(new_val)
            self.quality_label.config(text=f"{new_val}%")
            self._draw_quality_slider()



    def _create_action_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="3. 執行轉換", padding="15")
        frame.grid(row=2, column=0, sticky="ew")
        frame.grid_columnconfigure(0, weight=1)

        self.output_dir_label = ttk.Label(frame, text="尚未選擇輸出資料夾", wraplength=250, font=self.font_normal)
        self.output_dir_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        btn_output = ttk.Button(frame, text="💾 選擇輸出資料夾", command=self._select_output_folder)
        btn_output.grid(row=1, column=0, sticky="ew", pady=5)

        # self.start_button = ttk.Button(frame, text="⚡ 開始轉換", command=self._start_conversion, style="Accent.TButton")
        # self.start_button.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        self.start_button = self._create_blue_button(frame, "⚡ 開始轉換", self._start_conversion, width=100)
        self.start_button.grid(row=2, column=0, sticky="ew", pady=(10, 0))

    def _create_file_list_widgets(self, parent):
        self.file_list_frame = ttk.LabelFrame(parent, text="待處理檔案", padding="15")
        self.file_list_frame.grid(row=0, column=0, sticky="nsew")
        self.file_list_frame.grid_rowconfigure(0, weight=1)
        self.file_list_frame.grid_columnconfigure(0, weight=1)

        canvas = tk.Canvas(self.file_list_frame, borderwidth=0, background=self.style.lookup("TFrame", "background"))
        scrollbar = ttk.Scrollbar(self.file_list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        def _on_mousewheel(event):
            if event.num == 5 or event.delta < 0:
                canvas.yview_scroll(1, "units")
            elif event.num == 4 or event.delta > 0:
                canvas.yview_scroll(-1, "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)



    def _create_status_widgets(self, parent):
        frame = ttk.LabelFrame(parent, text="處理狀態", padding="15")
        frame.grid(row=2, column=0, sticky="ew", pady=(10, 0)) # Changed row to 2
        frame.grid_columnconfigure(0, weight=1)

        self.progress_var = tk.DoubleVar()
        self.progressbar = ttk.Progressbar(frame, variable=self.progress_var, maximum=100)
        self.progressbar.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        log_frame = ttk.Frame(frame)
        log_frame.grid(row=1, column=0, sticky="nsew")
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        self.log_tree = ttk.Treeview(log_frame, columns=("time", "date", "filename", "status", "duration"), show="headings", height=5)
        self.log_tree.heading("time", text="時間")
        self.log_tree.heading("date", text="日期")
        self.log_tree.heading("filename", text="檔案名稱")
        self.log_tree.heading("status", text="狀態")
        self.log_tree.heading("duration", text="耗時 (秒)")

        self.log_tree.column("time", width=80, anchor="center")
        self.log_tree.column("date", width=80, anchor="center")
        self.log_tree.column("filename", width=240)
        self.log_tree.column("status", width=80, anchor="center")
        self.log_tree.column("duration", width=80, anchor="center")

        self.log_tree.tag_configure("success", foreground="#4CAF50")
        self.log_tree.tag_configure("failure", foreground="#E57373")

        log_scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=log_scrollbar.set)
        self.log_tree.grid(row=0, column=0, sticky="nsew")
        log_scrollbar.grid(row=0, column=1, sticky="ns")

    def _log(self, message, is_error=False):
        print(f"LOG: {message}")

    def _update_file_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        


        # 決定要顯示哪個列表 (轉換後 vs. 來源)
        list_to_show = self.converted_files if self.converted_files else self.file_list
        is_converted_list = bool(self.converted_files)

        for i, f_path in enumerate(list_to_show):
            item_frame = ttk.Frame(self.scrollable_frame, padding=(0, 1, 0, 1))
            item_frame.pack(fill=tk.X, expand=True)
            
            if is_converted_list:
                item_frame.grid_columnconfigure(0, weight=1)
                label = ttk.Label(item_frame, text=os.path.basename(f_path), anchor="w", wraplength=450, justify=tk.LEFT)
                label.grid(row=0, column=0, sticky="ew", padx=(10, 0))
            else:
                # 顯示帶有縮圖和移除按鈕的來源檔案
                item_frame.grid_columnconfigure(1, weight=1)
                
                # 列表縮圖預覽
                try:
                    thumb_img = Image.open(f_path)
                    thumb_img.thumbnail((40, 40))
                    thumb_photo = ImageTk.PhotoImage(thumb_img)
                    self._thumbnail_cache.append(thumb_photo)
                    
                    thumb_label = tk.Label(item_frame, image=thumb_photo, bg="white")
                    thumb_label.grid(row=0, column=0, padx=5)
                    
                    if f_path.lower().endswith('.gif'):
                        self._animate_gif_small(thumb_label, f_path)
                except:
                    pass

                label = ttk.Label(item_frame, text=os.path.basename(f_path), anchor="w", wraplength=350, justify=tk.LEFT)
                label.grid(row=0, column=1, sticky="ew", padx=(5, 10))
                
                remove_canvas = tk.Canvas(item_frame, width=20, height=20, highlightthickness=0, background=self.style.lookup("TFrame", "background"))
                remove_canvas.grid(row=0, column=2, padx=(0, 5))

                circle_id = remove_canvas.create_oval(2, 2, 18, 18, outline="red", width=1.5)
                text_id = remove_canvas.create_text(10, 10, text="✕", fill="red", font=(self.font_family, 7, 'bold'), anchor="center")
                
                remove_canvas.bind("<Button-1>", lambda event, file_path=f_path: self._remove_file(file_path))
                remove_canvas.bind("<Enter>", lambda e, c=circle_id, t=text_id: (remove_canvas.itemconfig(c, outline="darkred"), remove_canvas.itemconfig(t, fill="darkred")))
                remove_canvas.bind("<Leave>", lambda e, c=circle_id, t=text_id: (remove_canvas.itemconfig(c, outline="red"), remove_canvas.itemconfig(t, fill="red")))

    def _remove_file(self, file_to_remove):
        try:
            self.file_list.remove(file_to_remove)
            self._update_file_list()
            self._log(f"已從列表中移除: {os.path.basename(file_to_remove)}")
        except ValueError:
            self._log(f"嘗試移除不存在的檔案: {os.path.basename(file_to_remove)}", is_error=True)

    def _select_files(self):
        # 如果選擇新檔案，重設轉換後的列表和 UI
        if self.converted_files:
            self.converted_files.clear()
            self.file_list_frame.config(text="待處理檔案")
        
        files = filedialog.askopenfilenames(title="選擇圖片檔案", filetypes=[("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.webp *.gif"), ("所有檔案", "*.*")])
        if files:
            normalized_files = [os.path.normpath(f) for f in files]
            self.file_list.extend(normalized_files)
            self.file_list = sorted(list(set(self.file_list)))
            self._update_file_list()
            self._log(f"已新增 {len(files)} 個檔案至列表。")

    def _select_output_folder(self):
        folder = filedialog.askdirectory(title="選擇輸出資料夾")
        if folder:
            self.output_dir = os.path.normpath(folder)
            self.output_dir_label.config(text=f"輸出至: {self.output_dir}")

    def _on_format_change(self, *args):
        is_jpeg = self.output_format_var.get().upper() == "JPEG"
        self.quality_enabled = is_jpeg
        state = "normal" if is_jpeg else "disabled"
        
        # Redraw slider to reflect enabled/disabled state
        self._draw_quality_slider()
        
        # ttk.Frame 無法直接禁用；改為禁用子元件 (excluding canvas which is handled manually)
        for child in self.quality_frame.winfo_children():
            if child != self.quality_slider_canvas:
                try:
                    child.configure(state=state)
                except:
                    pass 

    def _update_progress(self, result_data):
        self.after(0, self.__update_ui_progress, result_data)

    def __update_ui_progress(self, result_data):
        status = result_data.get("status")
        progress = result_data.get("progress", 0)
        self.progress_var.set(progress)

        if status in ["success", "failure"]:
            now = datetime.datetime.now()
            self.log_tree.insert("", tk.END, values=(
                now.strftime("%H:%M:%S"),
                now.strftime("%Y-%m-%d"),
                result_data.get("filename", "N/A"),
                "成功" if status == "success" else "失敗",
                f"{result_data.get('duration', 0):.2f}"
            ), tags=(status,))
            self.log_tree.see(self.log_tree.get_children()[-1])

        elif status == "finished":
            output_files = result_data.get("output_files", [])
            self._processing_finished(output_files)

    def _start_conversion(self):
        if not self.file_list:
            messagebox.showerror("錯誤", "尚未選擇任何輸入檔案。")
            return
            
        out_dir = self.output_dir
        if not out_dir:
            # 若需要則使用預設邏輯，或強制選擇
            if self.file_list:
                out_dir = os.path.join(os.path.dirname(self.file_list[0]), "converted")
            else:
                 return

        # 禁用所有動作按鈕
        # 禁用所有動作按鈕
        if hasattr(self, 'start_button'): self.start_button.config(state="disabled")
        
        settings = {
            "file_list": self.file_list,
            "output_dir": out_dir,
            "output_format": self.output_format_var.get(),
            "quality": self.quality_var.get(),
            "resize_options": {'type': 'none'},
            "progress_callback": self._update_progress
        }

        # 呼叫獨立的轉換處理函式來執行背景任務
        run_conversion_in_thread(settings)

    def _processing_finished(self, output_files):
        self.start_button.config(state="normal")
        messagebox.showinfo("成功", "圖片處理完成！")
        # 清空列表並重置 UI
        self.file_list = []
        self.converted_files = []
        self._update_file_list()
        
        # 重設選擇模式並更新列表
        self.file_list.clear()
        self.converted_files = output_files
        self.file_list_frame.config(text="轉換後檔案")
        self._update_file_list()
        
        self._log("轉換完成，顯示轉換後檔案列表。")




    # --- 旋轉圖片分頁功能 ---
    def _create_rotate_tab_content(self, parent):
        self.rotate_container = ttk.Frame(parent)
        self.rotate_container.pack(fill=tk.BOTH, expand=True)
        self.rotate_files_list = []
        self._show_rotate_landing()

    def _show_rotate_landing(self):
        for widget in self.rotate_container.winfo_children():
            widget.destroy()

        center_frame = ttk.Frame(self.rotate_container)
        center_frame.place(relx=0.5, rely=0.4, anchor="center")

        title_label = ttk.Label(center_frame, text="旋轉圖片", font=(self.font_family, 24, "bold"), foreground="#666")
        title_label.pack(pady=(0, 15))

        desc_text = "旋轉 JPG, PNG 或 GIF，\n每次旋轉 90° 或 180°。"
        desc_label = ttk.Label(center_frame, text=desc_text, justify="center", font=(self.font_family, 11), foreground="#555")
        desc_label.pack(pady=(0, 30))

        btn_frame = ttk.Frame(center_frame)
        btn_frame.pack()
        
        # 使用 ttk.Button 取代之前自訂的 Canvas 以維持一致性 (匹配第三張截圖)
        select_btn = ttk.Button(btn_frame, text="選擇多張圖片", style="Large.TButton", command=self._select_rotate_images)
        select_btn.pack()

        bottom_label = ttk.Label(center_frame, text="或者將多張圖片拖動到這裏", font=(self.font_family, 9), foreground="gray")
        bottom_label.pack(pady=(15, 0))

    def _select_rotate_images(self):
        files = filedialog.askopenfilenames(
            title="選擇要旋轉的圖片", 
            filetypes=[("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.gif"), ("所有檔案", "*.*")]
        )
        if files:
            self.rotate_files_list = list(files)
            self._show_rotate_options()

    def _show_rotate_options(self):
        for widget in self.rotate_container.winfo_children():
            widget.destroy()

        # 主要佈局：左側（預覽）+ 右側（側邊欄）
        self._rotate_original_images = [] # 清除舊狀態
        self.rotate_original_backup = []
        
        layout_frame = ttk.Frame(self.rotate_container)
        layout_frame.pack(fill=tk.BOTH, expand=True)

        # --- 左側：預覽區域 ---
        preview_frame = ttk.Frame(layout_frame)
        preview_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 標頭（預覽頂部）
        header_frame = ttk.Frame(preview_frame, padding="20")
        header_frame.pack(fill=tk.X)
        ttk.Label(header_frame, text="旋轉圖片", font=(self.font_family, 18, "bold"), foreground="#333").pack(anchor="center")
        
        ttk.Label(header_frame, text=f"已選擇 {len(self.rotate_files_list)} 張圖片", 
                              font=(self.font_family, 12), foreground="#555").pack(pady=(5, 0))

        # 預覽內容（畫布）
        canvas_preview_container = ttk.Frame(preview_frame, style="TFrame") # 置中容器
        canvas_preview_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        self.canvas_preview = tk.Canvas(canvas_preview_container, bg="#f5f7fa", highlightthickness=0)
        scrollbar_preview = ttk.Scrollbar(canvas_preview_container, orient="horizontal", command=self.canvas_preview.xview)
        
        self.scrollable_preview = tk.Frame(self.canvas_preview, bg="#f5f7fa")
        self.scrollable_preview.bind("<Configure>", lambda e: self.canvas_preview.configure(scrollregion=self.canvas_preview.bbox("all")))
        
        self.preview_window_id = self.canvas_preview.create_window((0, 0), window=self.scrollable_preview, anchor="nw")
        self.canvas_preview.configure(xscrollcommand=scrollbar_preview.set)

        self.canvas_preview.bind("<Configure>", self._center_preview_content)
        
        self.canvas_preview.pack(fill=tk.BOTH, expand=True)
        scrollbar_preview.pack(fill=tk.X)

        # 關閉按鈕（預覽區域右上角）
        close_btn = tk.Canvas(self.canvas_preview, width=24, height=24, bg="#f5f7fa", highlightthickness=0, cursor="hand2")
        close_btn.place(relx=1.0, y=10, x=-10, anchor="ne")
        close_btn.create_oval(2, 2, 22, 22, fill="#eee", outline="#ccc", tags="btn")
        close_btn.create_text(12, 12, text="✕", fill="#555", font=("Arial", 9, "bold"), tags="btn")
        close_btn.bind("<Button-1>", lambda e: self._show_rotate_landing())
        
        # 填入預覽內容
        self._load_rotate_previews()


        # --- 右側：側邊欄選項 ---
        sidebar_frame = tk.Frame(layout_frame, width=320, bg="white")
        sidebar_frame.pack(side=tk.RIGHT, fill=tk.Y)
        sidebar_frame.pack_propagate(False)
        
        # 分隔線
        ttk.Separator(sidebar_frame, orient='vertical').place(x=0, y=0, relheight=1.0)
        
        # 提示框
        tip_frame = tk.Frame(sidebar_frame, bg="#e3f2fd", padx=15, pady=15)
        tip_frame.pack(fill=tk.X, padx=20, pady=20)
        tk.Label(tip_frame, text="把滑鼠放在圖片上面，會出現一個圖示。點擊這個圖示即可旋轉圖片。", 
                 bg="#e3f2fd", fg="#1565c0", font=(self.font_family, 9), wraplength=250, justify="left").pack(anchor="w")

        # 頂部空間
        tk.Frame(sidebar_frame, bg="white", height=20).pack()

        # 旋轉控制
        rot_label_frame = tk.Frame(sidebar_frame, bg="white")
        rot_label_frame.pack(fill=tk.X, padx=20, pady=(30, 10))
        tk.Label(rot_label_frame, text="旋轉", bg="white", font=(self.font_family, 10, "bold"), fg="#333").pack(side=tk.LEFT)
        lbl_reset = tk.Label(rot_label_frame, text="全部重置", bg="white", font=(self.font_family, 9), fg="#4285f4", cursor="hand2")
        lbl_reset.pack(side=tk.RIGHT)
        lbl_reset.bind("<Button-1>", lambda e: self._reset_all_rotations())
        
        ctrl_frame = tk.Frame(sidebar_frame, bg="white")
        ctrl_frame.pack(fill=tk.X, padx=20)
        
        self.rotate_direction = tk.StringVar(value="right") # 預設

        def create_rot_btn(parent, text, direction, icon_char):
            # 按鈕容器
            btn = tk.Canvas(parent, height=50, bg="#f8f9fa", highlightthickness=0, cursor="hand2")
            btn.pack(fill=tk.X, pady=5)
            
            # 圖標框（左）
            btn.create_rectangle(0, 0, 50, 50, fill="#5c8add", outline="", tags="btn_item") # 圖標背景
            btn.create_text(25, 25, text=icon_char, fill="black", font=("Arial", 20), tags="btn_item")
            
            # 文字（右）
            btn.create_text(70, 25, text=text, fill="#333", font=(self.font_family, 10), anchor="w", tags="btn_item")
            
            # 懸停效果
            def on_enter(e): btn.configure(bg="#e8f0fe")
            def on_leave(e): btn.configure(bg="#f8f9fa")
            btn.bind("<Enter>", on_enter)
            btn.bind("<Leave>", on_leave)
            
            # 處理畫布及其項目的點擊
            def on_click(e): self._perform_single_step_rotate(direction)
            btn.bind("<Button-1>", on_click)
            btn.tag_bind("btn_item", "<Button-1>", on_click)
            return btn

        create_rot_btn(ctrl_frame, "右", "right", "↻")
        create_rot_btn(ctrl_frame, "左", "left", "↺")

        # 底部動作按鈕
        # 推至底部的間隔
        tk.Frame(sidebar_frame, bg="white").pack(fill=tk.BOTH, expand=True)
        
        action_btn_cnt = tk.Frame(sidebar_frame, bg="white", pady=20)
        action_btn_cnt.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.btn_rotate_action = tk.Canvas(action_btn_cnt, height=60, bg="white", highlightthickness=0, cursor="hand2")
        self.btn_rotate_action.pack(padx=20, fill=tk.X)
        
        self.btn_rotate_action = tk.Canvas(action_btn_cnt, height=60, bg="white", highlightthickness=0, cursor="hand2")
        self.btn_rotate_action.pack(padx=20, fill=tk.X)
        
        # 繪製藍色圓角矩形
        def round_rect(canvas, x, y, w, h, r, **kwargs):
             points = (x+r, y, x+r, y, x+w-r, y, x+w-r, y, x+w, y, x+w, y+r, x+w, y+r, x+w, y+h-r, x+w, y+h-r, x+w, y+h, x+w-r, y+h, x+w-r, y+h, x+r, y+h, x+r, y+h, x, y+h, x, y+h-r, x, y+h-r, x, y+r, x, y+r, x, y)
             return canvas.create_polygon(points, **kwargs, smooth=True)
        
        round_rect(self.btn_rotate_action, 2, 2, 276, 56, 10, fill="#4285f4", tags="action")
        self.btn_rotate_action.create_text(140, 30, text="下載旋轉後的圖片 ➔", fill="black", font=(self.font_family, 12, "bold"), tags="action")
        
        def on_action_click(e): self._perform_batch_rotate_save()
        self.btn_rotate_action.bind("<Button-1>", on_action_click)
        self.btn_rotate_action.tag_bind("action", "<Button-1>", on_action_click)

    def _reset_all_rotations(self):
        """從備份還原所有圖片"""
        if not self.rotate_original_backup: return
        
        self._rotate_original_images = [img.copy() for img in self.rotate_original_backup]
        self._load_rotate_previews()
        self._log("已重置所有旋轉設定。")

        
    def _center_preview_content(self, event):
        canvas_width = event.width
        content_width = self.scrollable_preview.winfo_reqwidth()
        if content_width < canvas_width:
             self.canvas_preview.coords(self.preview_window_id, (canvas_width - content_width) // 2, 0)
        else:
             self.canvas_preview.coords(self.preview_window_id, 0, 0)
             
    def _load_rotate_previews(self):
        self._rotate_thumbnail_cache = []
        if not self._rotate_original_images:
             init_load = True
        else:
             init_load = False

        self._rotate_preview_labels = []
        
        # 清除舊內容
        for widget in self.scrollable_preview.winfo_children():
            widget.destroy()

        # 在可滾動框架中置中容器
        center_container = ttk.Frame(self.scrollable_preview)
        center_container.pack(expand=True, pady=50)

        for i, file_path in enumerate(self.rotate_files_list):
            try:
                if init_load:
                    img = Image.open(file_path)
                    self._rotate_original_images.append(img.copy())
                    self.rotate_original_backup.append(img.copy())
                
                img = self._rotate_original_images[i]
                
                thumb_frame = tk.Frame(center_container, bg="white", padx=5, pady=5)
                thumb_frame.pack(side=tk.LEFT, padx=10)
                
                # 初始縮圖
                thumb_copy = img.copy()
                thumb_copy.thumbnail((150, 150))
                photo = ImageTk.PhotoImage(thumb_copy)
                self._rotate_thumbnail_cache.append(photo)
                
                img_label = tk.Label(thumb_frame, image=photo, bg="white")
                img_label.pack()
                self._rotate_preview_labels.append(img_label)
                
                # 若為 GIF，啟動動畫
                if file_path.lower().endswith('.gif'):
                    self._animate_gif(img_label, file_path)
                
                # 點擊單張旋轉
                img_label.bind("<Button-1>", lambda e, idx=i: self._rotate_single_image(idx))
                img_label.config(cursor="hand2")
                
                # 檔名
                fname = os.path.basename(file_path)
                if len(fname) > 12: fname = fname[:10] + "..."
                tk.Label(thumb_frame, text=fname, bg="white", font=(self.font_family, 8)).pack()
                
            except Exception as e:
                print(f"Error: {e}")

    def _animate_gif(self, label, file_path):
        """標籤的標準 GIF 動畫"""
        self._stop_animation(label)
        try:
            img = Image.open(file_path)
            frames = []
            for frame in ImageSequence.Iterator(img):
                f = frame.copy().convert("RGBA")
                f.thumbnail((150, 150))
                frames.append(ImageTk.PhotoImage(f))
            
            if not frames: return

            def update(idx):
                if not label.winfo_exists(): return
                label.configure(image=frames[idx])
                label.image = frames[idx]
                next_idx = (idx + 1) % len(frames)
                self._gif_animations[label] = {
                    'cancel_id': label.after(100, update, next_idx),
                    'frames': frames
                }
            
            update(0)
        except: pass

    def _animate_gif_small(self, label, file_path):
        """小列表縮圖的輔助函式"""
        self._stop_animation(label)
        try:
            img = Image.open(file_path)
            frames = []
            for frame in ImageSequence.Iterator(img):
                f = frame.copy().convert("RGBA")
                f.thumbnail((40, 40))
                frames.append(ImageTk.PhotoImage(f))
            
            if not frames: return

            def update(idx):
                if not label.winfo_exists(): return
                label.configure(image=frames[idx])
                label.image = frames[idx]
                next_idx = (idx + 1) % len(frames)
                self._gif_animations[label] = {
                    'cancel_id': label.after(100, update, next_idx),
                    'frames': frames
                }
            
            update(0)
        except: pass

    def _animate_gif_on_canvas(self, canvas, file_path, tag="preview_img"):
        """畫布螢幕的 GIF 動畫"""
        self._stop_animation(canvas)
        try:
            img = Image.open(file_path)
            
            # 需要畫布尺寸以適當縮放
            canvas.update_idletasks()
            cw, ch = canvas.winfo_width(), canvas.winfo_height()
            if cw <=1: cw, ch = 800, 600
            
            img_w, img_h = img.size
            scale = min(cw/img_w, ch/img_h, 1.0) * 0.9
            
            frames = []
            for frame in ImageSequence.Iterator(img):
                f = frame.copy().convert("RGBA")
                new_w, new_h = int(img_w * scale), int(img_h * scale)
                f = f.resize((new_w, new_h), Image.Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(f))
            
            if not frames: return
            
            last_size = (cw, ch)
            off_x, off_y = (cw - frames[0].width()) // 2, (ch - frames[0].height()) // 2

            def update(idx):
                if not canvas.winfo_exists(): return
                
                # 檢查尺寸是否改變
                canvas.update_idletasks()
                curr_w, curr_h = canvas.winfo_width(), canvas.winfo_height()
                nonlocal last_size, frames, off_x, off_y
                
                if (curr_w, curr_h) != last_size and curr_w > 1:
                    # 偵測到調整大小，重建影格
                    img_w, img_h = img.size
                    scale = min(curr_w/img_w, curr_h/img_h, 1.0) * 0.9
                    new_frames = []
                    for frame in ImageSequence.Iterator(img):
                        f = frame.copy().convert("RGBA")
                        nw, nh = int(img_w * scale), int(img_h * scale)
                        f = f.resize((nw, nh), Image.Resampling.LANCZOS)
                        new_frames.append(ImageTk.PhotoImage(f))
                    frames = new_frames
                    off_x, off_y = (curr_w - frames[0].width()) // 2, (curr_h - frames[0].height()) // 2
                    last_size = (curr_w, curr_h)

                canvas.delete("img_frame")
                canvas.create_image(off_x, off_y, anchor="nw", image=frames[idx], tags="img_frame")
                canvas.image_ref = frames[idx]
                
                canvas.tag_raise("crop_rect")
                canvas.tag_raise("overlay")
                
                next_idx = (idx + 1) % len(frames)
                self._gif_animations[canvas] = {
                    'cancel_id': canvas.after(100, update, next_idx),
                    'frames': frames,
                    'path': file_path
                }
            
            update(0)
        except: pass

    def _stop_animation(self, widget):
        if not hasattr(self, '_gif_animations'): self._gif_animations = {}
        if widget in self._gif_animations:
            try:
                widget.after_cancel(self._gif_animations[widget]['cancel_id'])
            except: pass
            del self._gif_animations[widget]


    def _rotate_single_image(self, index):
        # 將特定圖片向右旋轉 90 度
        if index < len(self._rotate_original_images):
             img = self._rotate_original_images[index]
             rotated = img.rotate(-90, expand=True) 
             self._rotate_original_images[index] = rotated
             
             # 僅更新此標籤的精確操作，以防止滾動重置
             label = self._rotate_preview_labels[index]
             # 停止任何動畫
             self._stop_animation(label)
             
             thumb_copy = rotated.copy()
             thumb_copy.thumbnail((150, 150))
             photo = ImageTk.PhotoImage(thumb_copy)
             # 更新快取以防止 GC
             self._rotate_thumbnail_cache[index] = photo
             label.configure(image=photo)
             label.image = photo
             
             # 若為 GIF，我們可能想要重新啟動動畫但旋轉之
             # 目前為求簡單，僅顯示靜態旋轉影格

    def _perform_single_step_rotate(self, direction):
        # 旋轉記憶體中的所有圖片（僅預覽，直到儲存）
        angle = -90 if direction == "right" else 90
        
        for i in range(len(self._rotate_original_images)):
            img = self._rotate_original_images[i]
            rotated = img.rotate(angle, expand=True)
            self._rotate_original_images[i] = rotated
        
        self._load_rotate_previews()
            
    def _perform_batch_rotate_save(self):
        # 儲存 self._rotate_original_images 中的所有圖片
        # 詢問輸出目錄
         output_dir = filedialog.askdirectory(title="選擇輸出資料夾")
         if not output_dir: return
         
         success_count = 0
         for i, img in enumerate(self._rotate_original_images):
             try:
                 src_path = self.rotate_files_list[i]
                 fname = os.path.basename(src_path)
                 name, ext = os.path.splitext(fname)
                 save_path = os.path.join(output_dir, f"{name}_rotated{ext}")
                 img.save(save_path)
                 success_count += 1
             except Exception as e:
                 print(e)
         
         messagebox.showinfo("成功", f"成功旋轉 {success_count} 張圖片！\n圖片已儲存至:\n{output_dir}")
         self._show_rotate_landing()
         
         

    def _show_rotate_result(self, count):
        """顯示旋轉結果"""
        for widget in self.rotate_container.winfo_children():
            widget.destroy()

        content = ttk.Frame(self.rotate_container)
        content.place(relx=0.5, rely=0.45, anchor="center")

        # 標題
        ttk.Label(content, text=f"成功旋轉 {count} 張圖片！", font=(self.font_family, 24, "bold"), foreground="#333").pack(pady=(0, 30))

        # 下載按鈕
        row1 = ttk.Frame(content)
        row1.pack(pady=20)
        
        # 返回箭頭
        arrow_canvas = tk.Canvas(row1, width=40, height=40, bg="#f0f0f0", highlightthickness=0, cursor="hand2")
        arrow_canvas.pack(side=tk.LEFT, padx=(0, 15))
        arrow_canvas.create_oval(2, 2, 38, 38, fill="#444")
        arrow_canvas.create_text(20, 20, text="←", fill="black", font=("Arial", 16, "bold"))
        arrow_canvas.bind("<Button-1>", lambda e: self._show_rotate_landing())

        # 藍色按鈕
        dl_btn = tk.Canvas(row1, width=350, height=60, bg="#f0f0f0", highlightthickness=0, cursor="hand2")
        dl_btn.pack(side=tk.LEFT)
        
        def round_rectangle(canvas, x1, y1, x2, y2, radius=25, **kwargs):
            points = [x1+radius, y1, x1+radius, y1, x2-radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y1+radius, x2, y2-radius, x2, y2-radius, x2, y2, x2-radius, y2, x2-radius, y2, x1+radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y2-radius, x1, y1+radius, x1, y1+radius, x1, y1]
            return canvas.create_polygon(points, **kwargs, smooth=True)

        round_rectangle(dl_btn, 2, 2, 348, 58, radius=10, fill="#4285f4", outline="")
        
        # 繪製圖標
        cx, cy = 90, 30
        dl_btn.create_line(cx, cy-10, cx, cy+5, fill="white", width=3, capstyle="round")
        dl_btn.create_line(cx-7, cy-2, cx, cy+5, cx+7, cy-2, fill="white", width=3, capstyle="round", joinstyle="round")
        dl_btn.create_line(cx-10, cy+5, cx-10, cy+12, cx+10, cy+12, cx+10, cy+5, fill="white", width=3, capstyle="round")
        
        dl_btn.create_text(210, 30, text="開啟輸出資料夾", fill="black", font=(self.font_family, 14, "bold"))
        dl_btn.bind("<Button-1>", lambda e: os.startfile(self.last_rotate_output) if os.name == 'nt' else None)

    def _reset_video_tab(self):
        # 若正在播放則停止
        if self.is_playing:
            self._toggle_play()
        
        # 清除子元件
        for widget in self.video_tab.winfo_children():
            widget.destroy()
            
        self._create_video_tab_content(self.video_tab)

    def _create_video_tab_content(self, parent):
        # 建立置中容器
        main_frame = ttk.Frame(parent)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 標題區
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(header_frame, text="影片截圖", font=(self.font_family, 18, "bold")).pack(side=tk.LEFT)
        
        # 影片控制區（選擇影片）
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.btn_select_video = ttk.Button(control_frame, text="選擇影片", command=self._select_video, style="Blue.TButton")
        self.btn_select_video.pack(side=tk.LEFT)
        
        self.video_info_label = ttk.Label(control_frame, text="尚未載入影片", font=self.font_normal, foreground="#555")
        self.video_info_label.pack(side=tk.LEFT, padx=15)

        # 預覽區（畫布）
        self.video_canvas = tk.Canvas(main_frame, bg="black", height=400)
        self.video_canvas.pack(fill=tk.BOTH, expand=True)

        # 播放/預覽控制（滑桿與儲存）
        bottom_frame = ttk.Frame(main_frame, padding="10")
        bottom_frame.pack(fill=tk.X)
        
        # 滑桿
        # Custom Slider (Canvas)
        self.video_slider_max = 100
        self.video_slider_var = tk.DoubleVar()
        self.video_slider_canvas = tk.Canvas(bottom_frame, height=20, bg=self.style.lookup("TFrame", "background"), highlightthickness=0, cursor="hand2")
        self.video_slider_canvas.pack(fill=tk.X, pady=(0, 10))
        
        self.video_slider_canvas.bind("<Button-1>", self._on_slider_interact)
        self.video_slider_canvas.bind("<B1-Motion>", self._on_slider_interact)
        self.video_slider_canvas.bind("<Configure>", lambda e: self._draw_video_slider())

        # 按鈕與資訊
        action_frame = ttk.Frame(bottom_frame)
        action_frame.pack(fill=tk.X)
        
        # 左側控制項
        left_controls = ttk.Frame(action_frame)
        left_controls.pack(side=tk.LEFT)

        self.btn_rewind = ttk.Button(left_controls, text="⏪ -5s", command=lambda: self._seek_relative(-5), state="disabled", width=8)
        self.btn_rewind.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_play_video = ttk.Button(left_controls, text="▶ 播放", command=self._toggle_play, state="disabled", width=8)
        self.btn_play_video.pack(side=tk.LEFT, padx=(0, 5))

        self.btn_forward = ttk.Button(left_controls, text="+5s ⏩", command=lambda: self._seek_relative(5), state="disabled", width=8)
        self.btn_forward.pack(side=tk.LEFT, padx=(0, 10))

        self.frame_info_label = ttk.Label(left_controls, text="Frame: 0 / 0", font=self.font_normal)
        self.frame_info_label.pack(side=tk.LEFT)

        # self.btn_save_frame = ttk.Button(action_frame, text="儲存截圖", command=self._save_screenshot, state="disabled")
        # self.btn_save_frame.pack(side=tk.RIGHT)
        # 使用自訂藍色按鈕 (需要手動控制狀態，或者直接不禁用，點擊時檢查)
        # 由於 Canvas 模擬按鈕較難直接禁用 (state="disabled")，我們先保持可用但內部檢查
        self.btn_save_frame_canvas = self._create_blue_button(action_frame, "儲存截圖", self._save_screenshot, height=35, width=120)
        self.btn_save_frame_canvas.pack(side=tk.RIGHT)
        # 我們不使用 ttk 的 state，而是保留此變數以相容舊程式碼引用
        self.btn_save_frame = self.btn_save_frame_canvas 


    def _select_video(self):
        file_path = filedialog.askopenfilename(
            title="選擇影片檔案",
            filetypes=[("Video Files", "*.mp4 *.avi *.mov *.mkv *.wmv"), ("All Files", "*.*")]
        )
        if file_path:
            try:
                info = self.video_processor.load_video(file_path)
                self.video_info_label.config(text=f"已載入: {os.path.basename(file_path)}")
                
                # 更新控制項
                self.video_slider_max = info["total_frames"] - 1
                self.video_slider_var.set(0)
                self._draw_video_slider() # 初始繪製
                self.btn_save_frame.configure(state="normal")
                self.btn_play_video.configure(state="normal") # 啟用播放按鈕
                self.btn_rewind.configure(state="normal")
                self.btn_forward.configure(state="normal")
                
                # 顯示第一幀
                self._update_video_preview(0)

                
            except Exception as e:
                messagebox.showerror("錯誤", f"無法載入影片:\n{e}")

    def _draw_video_slider(self):
        cv = self.video_slider_canvas
        if not cv.winfo_exists(): return
        
        w = cv.winfo_width()
        h = cv.winfo_height()
        if w <= 1: return # Not ready
        
        cv.delete("all")
        
        # Calculate positions
        current = self.video_slider_var.get()
        ratio = current / self.video_slider_max if self.video_slider_max > 0 else 0
        
        margin_x = 10
        track_w = w - 2 * margin_x
        cy = h / 2
        
        thumb_x = margin_x + track_w * ratio
        
        # Draw Background Track (Gray)
        cv.create_line(margin_x, cy, w - margin_x, cy, fill="#e0e0e0", width=4, capstyle="round")
        
        # Draw Progress Track (Blue)
        if ratio > 0:
            cv.create_line(margin_x, cy, thumb_x, cy, fill="#4285f4", width=4, capstyle="round")
            
        # Draw Thumb (Circle)
        r = 5
        cv.create_oval(thumb_x - r, cy - r, thumb_x + r, cy + r, fill="white", outline="#4285f4", width=2)

    def _on_slider_interact(self, event):
        if not hasattr(self, 'video_processor') or not self.video_processor.cap:
             return
             
        cv = self.video_slider_canvas
        w = cv.winfo_width()
        margin_x = 10
        track_w = w - 2 * margin_x
        
        x = event.x - margin_x
        ratio = max(0, min(1, x / track_w))
        
        new_val = ratio * self.video_slider_max
        self.video_slider_var.set(new_val)
        
        # Update preview and redraw slider
        self._update_video_preview_event(new_val)
        self._draw_video_slider()

    def _update_video_preview_event(self, val):
        # 滑桿事件包裝器，拖曳時暫停播放
        if self.is_playing:
            self._toggle_play() # 若使用者拖曳滑桿則暫停
        self._update_video_preview(val)

    def _update_video_preview(self, val):

        frame_idx = int(float(val))
        
        # 更新影格資訊標籤
        total = self.video_processor.total_frames
        fps = self.video_processor.fps
        timestamp = frame_idx / fps if fps > 0 else 0
        self.frame_info_label.config(text=f"Frame: {frame_idx} / {total}  ({timestamp:.2f}s)")

        # 取得影格
        image = self.video_processor.get_frame(frame_idx)
        if image:
            self._display_video_frame(image)
        
        # 儲存目前圖片以供存檔
        self._current_video_frame = image
        
        # 確保滑桿與值同步 (若是從播放器更新)
        # 注意：避免無窮迴圈，只有當數值改變時才需要擔心
        if self.video_slider_var.get() != frame_idx:
             self.video_slider_var.set(frame_idx)
             
        self._draw_video_slider()

    def _seek_relative(self, seconds):
        if not hasattr(self, 'video_processor') or not self.video_processor.cap:
             return
             
        # 計算影格數 delta
        fps = self.video_processor.fps if self.video_processor.fps > 0 else 30
        delta_frames = int(seconds * fps)
        
        current_frame = self.video_slider_var.get()
        new_frame_idx = max(0, min(self.video_processor.total_frames - 1, current_frame + delta_frames))
        
        # 更新滑桿與預覽 (這會自動更新顯示與標籤)
        self.video_slider_var.set(new_frame_idx)
        self._update_video_preview(new_frame_idx)
        self._draw_video_slider()

    def _display_video_frame(self, image):
        # 調整大小以適應畫布並維持長寬比
        canvas_w = self.video_canvas.winfo_width()
        canvas_h = self.video_canvas.winfo_height()
        
        if canvas_w < 10 or canvas_h < 10:
             # 若畫布尚未繪製，猜測或等待？
             # 僅使用合理的預設值以避免崩潰
             canvas_w = 600
             canvas_h = 400
        
        img_w, img_h = image.size
        scale = min(canvas_w / img_w, canvas_h / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self._video_tk_image = ImageTk.PhotoImage(resized) # 保留引用
        
        # 置中
        off_x = (canvas_w - new_w) // 2
        off_y = (canvas_h - new_h) // 2
        
        self.video_canvas.delete("all")
        self.video_canvas.create_image(off_x, off_y, anchor="nw", image=self._video_tk_image)

        # 繪製關閉按鈕
        padding = 15
        btn_r = 14
        cx_btn = canvas_w - padding - btn_r
        cy_btn = padding + btn_r
        
        # 圓圈
        self.video_canvas.create_oval(cx_btn-btn_r, cy_btn-btn_r, cx_btn+btn_r, cy_btn+btn_r, fill="#eee", outline="#ccc", tags=("vid_overlay", "close_btn_bg"))
        # X
        self.video_canvas.create_text(cx_btn, cy_btn, text="✕", fill="#555", font=("Arial", 10, "bold"), tags=("vid_overlay", "close_btn_text"))
        
        # 綁定
        self.video_canvas.tag_bind("close_btn_bg", "<Button-1>", lambda e: self._reset_video_tab())
        self.video_canvas.tag_bind("close_btn_text", "<Button-1>", lambda e: self._reset_video_tab())
        
        self.video_canvas.tag_bind("close_btn_bg", "<Enter>", lambda e: self.video_canvas.itemconfig("close_btn_bg", fill="#e0e0e0"))
        self.video_canvas.tag_bind("close_btn_bg", "<Leave>", lambda e: self.video_canvas.itemconfig("close_btn_bg", fill="#eee"))
        self.video_canvas.tag_bind("close_btn_text", "<Enter>", lambda e: self.video_canvas.itemconfig("close_btn_bg", fill="#e0e0e0"))
        self.video_canvas.tag_bind("close_btn_text", "<Leave>", lambda e: self.video_canvas.itemconfig("close_btn_bg", fill="#eee"))

    def _toggle_play(self):
        if not hasattr(self, 'video_processor') or not self.video_processor.cap:
            return
            
        if self.is_playing:
            # 暫停
            self.is_playing = False
            self.btn_play_video.configure(text="▶ 播放")
            if self.play_job:
                self.after_cancel(self.play_job)
                self.play_job = None
        else:
            # 播放
            self.is_playing = True
            self.btn_play_video.configure(text="⏸ 暫停")
            self._video_loop()

    def _video_loop(self):
        if not self.is_playing:
            return

        image, idx = self.video_processor.get_next_frame()
        
        if image:
            # 更新滑桿數值並重新繪製滑桿視覺
            self.video_slider_var.set(idx)
            self._draw_video_slider()
            
            # Update display
            self._display_video_frame(image) # Directly display, skip re-seek
            self._current_video_frame = image
            
            # Update label
            total = self.video_processor.total_frames
            fps = self.video_processor.fps
            timestamp = idx / fps if fps > 0 else 0
            self.frame_info_label.config(text=f"Frame: {idx} / {total}  ({timestamp:.2f}s)")
            
            # Schedule next frame
            # FPS control: 1000ms / fps
            delay = int(1000 / (self.video_processor.fps if self.video_processor.fps > 0 else 30))
            if delay < 1: delay = 1
            self.play_job = self.after(delay, self._video_loop)
        else:
            # End of video
            self._toggle_play()

    def _save_screenshot(self):

        if hasattr(self, '_current_video_frame') and self._current_video_frame:
            file_path = filedialog.asksaveasfilename(
                title="儲存截圖",
                defaultextension=".jpg",
                filetypes=[("JPEG", "*.jpg"), ("PNG", "*.png")]
            )
            if file_path:
                try:
                    self._current_video_frame.save(file_path)
                    messagebox.showinfo("成功", f"圖片已儲存至:\n{file_path}")
                    self._reset_video_tab()
                except Exception as e:
                    messagebox.showerror("錯誤", f"儲存失敗:\n{e}")

