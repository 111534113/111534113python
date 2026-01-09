#輔助/備份
    def _add_files(self):
        files = filedialog.askopenfilenames(title="選擇圖片", filetypes=[("圖片檔案", "*.jpg *.jpeg *.png *.bmp *.webp")])
        if files:
            for f in files:
                if f not in self.file_list:
                    self.file_list.append(f)
                    size = os.path.getsize(f) / 1024 # KB
                    self.tree.insert("", tk.END, values=(f, f"{size:.1f} KB"))

    def _clear_list(self):
        self.file_list = []
        for item in self.tree.get_children():
            self.tree.delete(item)

    def _select_output_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.output_dir = d
            self.lbl_output.config(text=d)

    def _start_conversion(self):
        if not self.file_list:
            messagebox.showwarning("警告", "請先選擇圖片")
            return
            
        out_dir = self.output_dir
        if not out_dir:
            # Default to first file's dir + /converted
            first = self.file_list[0]
            out_dir = os.path.join(os.path.dirname(first), "converted")
            
        fmt = self.format_var.get()
        
        # Simple settings for now, mirroring logic that likely existed
        settings = {
            "file_list": self.file_list,
            "output_dir": out_dir,
            "output_format": fmt,
            "quality": 95,
            "resize_options": {"type": "none"}, # No resize in simple convert
            "progress_callback": self._on_progress # Need to check if this exists or just print
        }
        
        # Use existing handler
        run_conversion_in_thread(settings)
        
    def _on_progress(self, info):
        # minimal implementation if missing
        if info['status'] == 'finished':
            messagebox.showinfo("完成", info['message'])
        elif info['status'] == 'failure':
            print(f"Error: {info['message']}")
