import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from ttkthemes import ThemedTk
from PIL import Image, ImageTk, ImageEnhance, ImageFilter, ImageOps, ImageDraw, ImageFont
import os

# Matplotlib untuk Histogram
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class PhotoEditorFinal:
    def __init__(self, root):
        self.root = root
        self.root.set_theme("arc") 
        self.root.title("Foto Editor")
        self.root.geometry("1366x768")

        # Variabel State Aplikasi
        self.image_path = None
        self.original_image = None
        self.processed_image = None
        self.image_tk = None
        self.history = []
        self.is_cropping = False
        
        # Variabel untuk cropping
        self.crop_start_x = None
        self.crop_start_y = None
        self.crop_rectangle = None
        
        self.load_icons()
        self.create_layout()
        self.create_widgets()
        self.bind_shortcuts()

    def load_icons(self):
        # Fungsi untuk memuat semua ikon yang dibutuhkan
        try:
            self.icon_open = self.create_icon("icons/open-folder.png")
            self.icon_save = self.create_icon("icons/save.png")
            self.icon_reset = self.create_icon("icons/reset.png")
            self.icon_undo = self.create_icon("icons/undo.png")
            self.icon_crop = self.create_icon("icons/crop.png")
            self.icon_histogram = self.create_icon("icons/histogram.png")
            self.icon_text = self.create_icon("icons/text.png")
            self.icon_flip_horizontal = self.create_icon("icons/flip-horizontal.png")
            self.icon_flip_vertical = self.create_icon("icons/flip-vertical.png")
        except Exception as e:
            messagebox.showwarning("Peringatan Ikon", f"Beberapa ikon tidak ditemukan: {e}\nTombol akan tetap berfungsi tanpa ikon.")

    def create_icon(self, path):
        return ImageTk.PhotoImage(Image.open(path).resize((24, 24), Image.LANCZOS))

    def bind_shortcuts(self):
        self.root.bind("<Control-o>", lambda event: self.open_image())
        self.root.bind("<Control-s>", lambda event: self.save_image())
        self.root.bind("<Control-z>", lambda event: self.undo_action())
    
    def update_status(self, text):
        self.status_bar.config(text=text)

    def create_layout(self):
        self.control_container = ttk.Frame(self.root, width=320)
        self.control_container.pack(side=tk.LEFT, fill=tk.Y, padx=(10,0), pady=10)
        self.control_container.pack_propagate(False)
        self.canvas = tk.Canvas(self.control_container, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.control_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        self.scrollable_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.scrollable_frame.bind("<Configure>", self.on_frame_configure)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        self.root.bind('<Enter>', self._bind_mouse)
        self.root.bind('<Leave>', self._unbind_mouse)
        self.image_frame = ttk.Frame(self.root)
        self.image_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.status_bar = ttk.Label(self.root, text="Selamat Datang di Foto Editor Final v2.1!", anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        self.image_label = tk.Canvas(self.image_frame, background="#2E2E2E", highlightthickness=0)
        self.image_label.pack(expand=True, fill=tk.BOTH)

    def create_widgets(self):
        # << FIX: Semua widget sekarang dimasukkan ke self.scrollable_frame, bukan self.control_frame >>
        
        # Frame File & Riwayat
        file_frame = ttk.LabelFrame(self.scrollable_frame, text="File & Riwayat")
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(file_frame, text=" Buka (Ctrl+O)", image=getattr(self, 'icon_open', None), compound=tk.LEFT, command=self.open_image).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(file_frame, text=" Simpan (Ctrl+S)", image=getattr(self, 'icon_save', None), compound=tk.LEFT, command=self.save_image).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(file_frame, text=" Undo (Ctrl+Z)", image=getattr(self, 'icon_undo', None), compound=tk.LEFT, command=self.undo_action).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(file_frame, text=" Reset ke Asli", image=getattr(self, 'icon_reset', None), compound=tk.LEFT, command=self.reset_image).pack(fill=tk.X, padx=10, pady=5)

        # Frame Alat Pro & Kreatif
        pro_tools_frame = ttk.LabelFrame(self.scrollable_frame, text="Alat Profesional & Kreatif")
        pro_tools_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Button(pro_tools_frame, text=" Potong Gambar (Crop)", image=getattr(self, 'icon_crop', None), compound=tk.LEFT, command=self.toggle_crop_mode).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(pro_tools_frame, text=" Tampilkan Histogram", image=getattr(self, 'icon_histogram', None), compound=tk.LEFT, command=self.show_histogram).pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(pro_tools_frame, text=" Tambah Teks", image=getattr(self, 'icon_text', None), compound=tk.LEFT, command=self.open_text_dialog).pack(fill=tk.X, padx=10, pady=5)

        # Frame Penyesuaian Gambar
        adjust_frame = ttk.LabelFrame(self.scrollable_frame, text="Penyesuaian Gambar")
        adjust_frame.pack(fill=tk.X, padx=10, pady=10)
        adjust_frame.columnconfigure(1, weight=1)
        
        ttk.Label(adjust_frame, text="Kecerahan:").grid(row=0, column=0, sticky="w", padx=5)
        self.brightness_slider = ttk.Scale(adjust_frame, from_=0.1, to=2.5, orient=tk.HORIZONTAL, command=self.schedule_adjustment)
        self.brightness_slider.set(1.0)
        self.brightness_slider.grid(row=0, column=1, sticky="ew")

        ttk.Label(adjust_frame, text="Kontras:").grid(row=1, column=0, sticky="w", padx=5)
        self.contrast_slider = ttk.Scale(adjust_frame, from_=0.1, to=2.5, orient=tk.HORIZONTAL, command=self.schedule_adjustment)
        self.contrast_slider.set(1.0)
        self.contrast_slider.grid(row=1, column=1, sticky="ew")
        
        ttk.Label(adjust_frame, text="Angkat Shadow:").grid(row=2, column=0, sticky="w", padx=5, pady=(10,0))
        self.shadow_lift_slider = ttk.Scale(adjust_frame, from_=0, to=50, orient=tk.HORIZONTAL, command=self.schedule_adjustment)
        self.shadow_lift_slider.set(0)
        self.shadow_lift_slider.grid(row=2, column=1, sticky="ew", pady=(10,0))

        ttk.Label(adjust_frame, text="Turunkan Highlight:").grid(row=3, column=0, sticky="w", padx=5)
        self.highlight_recovery_slider = ttk.Scale(adjust_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=self.schedule_adjustment)
        self.highlight_recovery_slider.set(0)
        self.highlight_recovery_slider.grid(row=3, column=1, sticky="ew")
        
        # Frame Transformasi
        transform_frame = ttk.LabelFrame(self.scrollable_frame, text="Transformasi")
        transform_frame.pack(fill=tk.X, padx=10, pady=10)
        transform_frame.columnconfigure((0,1), weight=1)
        ttk.Button(transform_frame, text="Putar Kiri", command=lambda: self.rotate_image(90)).grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ttk.Button(transform_frame, text="Putar Kanan", command=lambda: self.rotate_image(-90)).grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(transform_frame, text="Balik Horizontal", image=getattr(self, 'icon_flip_horizontal', None), compound=tk.LEFT, command=lambda: self.flip_image("horizontal")).grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        ttk.Button(transform_frame, text="Balik Vertikal", image=getattr(self, 'icon_flip_vertical', None), compound=tk.LEFT, command=lambda: self.flip_image("vertical")).grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(transform_frame, text="Reset Transformasi", command=self.reset_transformations).grid(row=2, column=0, columnspan=2, sticky="ew", padx=2, pady=5)
        
        # Frame Filter & Efek
        filter_frame = ttk.LabelFrame(self.scrollable_frame, text="Filter & Efek")
        filter_frame.pack(fill=tk.X, padx=10, pady=10)
        filter_frame.columnconfigure((0,1), weight=1)
        ttk.Button(filter_frame, text="Grayscale", command=lambda: self.apply_filter("grayscale")).grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(filter_frame, text="Blur", command=lambda: self.apply_filter("blur")).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(filter_frame, text="Sharpen", command=lambda: self.apply_filter("sharpen")).grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        ttk.Button(filter_frame, text="Edge Enhance", command=lambda: self.apply_filter("edge_enhance")).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Button(filter_frame, text="Sepia", command=lambda: self.apply_filter("sepia")).grid(row=2, column=0, columnspan=2, padx=5, pady=5, sticky="ew")
        ttk.Button(filter_frame, text="Invert (Negatif)", command=lambda: self.apply_filter("invert")).grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="ew")

    def on_frame_configure(self, event):
        """Reset scroll region untuk mencakup seluruh frame internal"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_canvas_configure(self, event):
        """Membuat lebar frame internal sama dengan lebar canvas"""
        self.canvas.itemconfig(self.scrollable_frame_id, width=event.width)

    def _on_mousewheel(self, event):
        """Fungsi scroll dengan roda mouse"""
        # Arah scroll berbeda di Windows vs Linux/macOS
        if os.name == 'nt':
            self.canvas.yview_scroll(-1 * (event.delta // 120), "units")
        else:
            if event.num == 4:
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                self.canvas.yview_scroll(1, "units")

    def _bind_mouse(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mouse(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")

    def bind_shortcuts(self):
        # Mengikat shortcut keyboard ke fungsi
        self.root.bind("<Control-o>", lambda event: self.open_image())
        self.root.bind("<Control-s>", lambda event: self.save_image())
        self.root.bind("<Control-z>", lambda event: self.undo_action())
    
    def update_status(self, text):
        # Memperbarui teks di status bar bawah
        self.status_bar.config(text=text)

    def open_image(self):
        self.image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.bmp;*.gif")])
        if self.image_path:
            self.original_image = Image.open(self.image_path)
            self.history = [] 
            self.reset_image(save_state=False) # Tidak perlu save state saat membuka gambar baru
            self.update_status(f"Gambar dimuat: {os.path.basename(self.image_path)}")

    def save_image(self):
        if not self.processed_image:
            messagebox.showwarning("Peringatan", "Tidak ada gambar untuk disimpan.")
            return
        
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG file", "*.png"), ("JPEG file", "*.jpg")])
        if save_path:
            try:
                # Pastikan menyimpan dalam mode RGB untuk format JPG
                save_image = self.processed_image.copy()
                if save_path.lower().endswith(('.jpg', '.jpeg')):
                    if save_image.mode != 'RGB':
                        save_image = save_image.convert('RGB')
                
                save_image.save(save_path)
                self.update_status(f"Gambar berhasil disimpan di {os.path.basename(save_path)}")
                messagebox.showinfo("Sukses", "Gambar berhasil disimpan!")
            except Exception as e:
                messagebox.showerror("Error", f"Gagal menyimpan gambar: {e}")

    def save_state(self):
        # << FIX: Sekarang menyimpan state transformed_image >>
        if self.transformed_image:
            self.history.append(self.transformed_image.copy())
            self.history = self.history[-10:]

    def undo_action(self):
        # << FIX: Undo sekarang mengembalikan transformed_image, lalu menerapkan penyesuaian >>
        if self.history:
            self.transformed_image = self.history.pop()
            self.apply_all_adjustments() # Terapkan kembali penyesuaian ke state yang sudah di-undo
            self.display_image()
            self.update_status("Langkah terakhir dibatalkan (Undo).")
        else:
            self.update_status("Tidak ada lagi langkah untuk dibatalkan.")

    def reset_image(self, save_state=True):
        # << FIX: Mereset semua state gambar dan slider >>
        if self.original_image:
            if save_state: self.save_state()
            self.transformed_image = self.original_image.copy()
            self.processed_image = self.original_image.copy()
            self.reset_sliders()
            self.display_image()
            self.update_status("Gambar & semua setelan direset.")

    def reset_transformations(self):
        if not self.original_image: return
        self.save_state()
        self.transformed_image = self.original_image.copy()
        self.apply_all_adjustments() # Terapkan kembali penyesuaian ke gambar yang transformasinya direset
        self.display_image()
        self.update_status("Transformasi (rotasi, flip, crop) direset.")
    
    def reset_sliders(self):
        # Helper untuk mereset semua slider ke nilai default
        self.brightness_slider.set(1.0)
        self.contrast_slider.set(1.0)
        self.black_level_slider.set(0)
        self.white_level_slider.set(0)

    def display_image(self):
        if self.processed_image:
            self.image_label.delete("all")
            img_w, img_h = self.processed_image.size
            canvas_w = self.image_label.winfo_width()
            canvas_h = self.image_label.winfo_height()

            if canvas_w < 20 or canvas_h < 20: return # Hindari error saat window terlalu kecil

            ratio = min(canvas_w / img_w, canvas_h / img_h)
            new_w, new_h = int(img_w * ratio), int(img_h * ratio)

            display_img = self.processed_image.resize((new_w, new_h), Image.LANCZOS)
            self.image_tk = ImageTk.PhotoImage(display_img)
            
            x_pos = (canvas_w - new_w) // 2
            y_pos = (canvas_h - new_h) // 2
            self.image_label.create_image(x_pos, y_pos, anchor=tk.NW, image=self.image_tk)

    _after_id = None
    def schedule_adjustment(self, event=None):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self._after_id = self.root.after(250, self.apply_all_adjustments)
    
    # << FUNGSI LENGKAP YANG SUDAH DIPERBAIKI >>
    def apply_all_adjustments(self):
        if not self.transformed_image: return
        
        # Mulai dari gambar yang sudah ditransformasi
        temp_image = self.transformed_image.copy()
        
        # --- TAHAP 1: Kecerahan & Kontras (Global) ---
        brightness = self.brightness_slider.get()
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(temp_image)
            temp_image = enhancer.enhance(brightness)

        contrast = self.contrast_slider.get()
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(temp_image)
            temp_image = enhancer.enhance(contrast)

        # --- TAHAP 2: Pemulihan Highlight (Metode Tone Curve) ---
        # Menggunakan self.highlight_recovery_slider
        highlight_recovery = self.highlight_recovery_slider.get()
        if highlight_recovery > 0:
            # Semakin tinggi nilainya, semakin kuat highlight ditekan
            factor = 1.0 - (highlight_recovery / 150.0) 
            
            # Membuat lookup table (LUT)
            lut = []
            for i in range(256):
                if i > 128:
                    val = 128 + (i - 128) ** factor
                    lut.append(int(val))
                else:
                    lut.append(i)
            
            if temp_image.mode != 'L':
                temp_image = temp_image.convert('RGB')
                
                # Terapkan LUT ke setiap channel warna
                r, g, b = temp_image.split()
                r = r.point(lut)
                g = g.point(lut)
                b = b.point(lut)
                temp_image = Image.merge('RGB', (r, g, b))
            else:
                 temp_image = temp_image.point(lut)

        shadow_lift = self.shadow_lift_slider.get() / 100.0
        if shadow_lift > 0:
             temp_image = ImageOps.autocontrast(temp_image, cutoff=(shadow_lift, 0))

        # Simpan hasil akhir ke processed_image dan tampilkan
        self.processed_image = temp_image 
        self.display_image()

    def flip_image(self, direction):
        if not self.transformed_image: return
        self.save_state()
        if direction == "horizontal":
            self.transformed_image = ImageOps.mirror(self.transformed_image) # << FIX
        elif direction == "vertical":
            self.transformed_image = ImageOps.flip(self.transformed_image) # << FIX
        self.apply_all_adjustments() # << FIX
        self.display_image()
        self.update_status(f"Gambar dibalik secara {direction}.")

    def rotate_image(self, angle_degrees):
        if not self.transformed_image: return
        self.save_state()
        self.transformed_image = self.transformed_image.rotate(angle_degrees, expand=True) # << FIX
        self.apply_all_adjustments() # << FIX
        self.display_image()
        self.update_status(f"Gambar diputar {angle_degrees} derajat.")

    def open_text_dialog(self):
        if not self.processed_image: return

        dialog = tk.Toplevel(self.root)
        dialog.title("Tambah Teks")
        dialog.geometry("300x200")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Teks:").pack(padx=10, pady=5)
        text_entry = ttk.Entry(dialog, width=40)
        text_entry.pack(padx=10)

        ttk.Label(dialog, text="Ukuran Font:").pack(padx=10, pady=5)
        size_entry = ttk.Entry(dialog)
        size_entry.insert(0, "48")
        size_entry.pack(padx=10)

        color_value = ["#FFFFFF"]
        def choose_color():
            color_code = colorchooser.askcolor(title="Pilih Warna Teks")
            if color_code:
                color_value[0] = color_code[1]

        ttk.Button(dialog, text="Pilih Warna", command=choose_color).pack(pady=10)
        
        def on_ok():
            text = text_entry.get()
            try:
                size = int(size_entry.get())
            except ValueError:
                size = 48 # Default jika input tidak valid
            color = color_value[0]
            dialog.destroy()
            self.prompt_for_text_placement(text, size, color)
        
        ttk.Button(dialog, text="OK", command=on_ok).pack(pady=10)

    def prompt_for_text_placement(self, text, size, color):
        self.update_status("Klik pada gambar untuk menempatkan teks.")
        self.image_label.config(cursor="xterm")
        self.image_label.bind("<ButtonPress-1>", lambda event: self.place_text(event, text, size, color))
    
    def place_text(self, event, text, size, color):
        self.image_label.unbind("<ButtonPress-1>")
        self.image_label.config(cursor="")
        
        # << FIX: Koordinat sekarang dihitung berdasarkan transformed_image >>
        canvas_w = self.image_label.winfo_width()
        canvas_h = self.image_label.winfo_height()
        img_w, img_h = self.transformed_image.size 
        ratio = min(canvas_w / img_w, canvas_h / img_h)
        canvas_x_offset = (canvas_w - int(img_w * ratio)) // 2
        canvas_y_offset = (canvas_h - int(img_h * ratio)) // 2

        real_x = int((event.x - canvas_x_offset) / ratio)
        real_y = int((event.y - canvas_y_offset) / ratio)
        
        self.save_state()
        # << FIX: Teks digambar pada transformed_image >>
        draw = ImageDraw.Draw(self.transformed_image) 
        try:
            font = ImageFont.truetype("arial.ttf", size)
        except IOError:
            font = ImageFont.load_default()
            self.update_status("Peringatan: arial.ttf tidak ditemukan, menggunakan font default.")

        draw.text((real_x, real_y), text, font=font, fill=color)
        
        # << FIX: Terapkan kembali penyesuaian slider setelah menambahkan teks >>
        self.apply_all_adjustments() 
        self.display_image()
        self.update_status("Teks ditambahkan.")

    def toggle_crop_mode(self):
        self.is_cropping = not self.is_cropping
        if self.is_cropping:
            self.update_status("Mode Crop Aktif: Klik dan tarik pada gambar untuk memilih area.")
            self.image_label.config(cursor="cross")
            self.image_label.bind("<ButtonPress-1>", self.start_crop)
            self.image_label.bind("<B1-Motion>", self.drag_crop)
            self.image_label.bind("<ButtonRelease-1>", self.end_crop)
        else:
            self.update_status("Mode Crop Dinonaktifkan.")
            self.image_label.config(cursor="")
            self.image_label.unbind("<ButtonPress-1>")
            self.image_label.unbind("<B1-Motion>")
            self.image_label.unbind("<ButtonRelease-1>")
            if self.crop_rectangle: self.image_label.delete(self.crop_rectangle)

    def start_crop(self, event):
        self.crop_start_x = event.x
        self.crop_start_y = event.y
        if self.crop_rectangle: self.image_label.delete(self.crop_rectangle)
        self.crop_rectangle = self.image_label.create_rectangle(self.crop_start_x, self.crop_start_y, self.crop_start_x, self.crop_start_y, outline="red", dash=(4,4))

    def drag_crop(self, event):
        if self.crop_rectangle: self.image_label.coords(self.crop_rectangle, self.crop_start_x, self.crop_start_y, event.x, event.y)

    def end_crop(self, event):
        if self.crop_rectangle:
            x1, y1, x2, y2 = self.image_label.coords(self.crop_rectangle)
            self.image_label.delete(self.crop_rectangle)
            self.crop_rectangle = None
            
            # << FIX: Koordinat sekarang dihitung berdasarkan transformed_image >>
            canvas_w = self.image_label.winfo_width()
            canvas_h = self.image_label.winfo_height()
            img_w, img_h = self.transformed_image.size
            ratio = min(canvas_w / img_w, canvas_h / img_h)
            new_w, new_h = int(img_w * ratio), int(img_h * ratio)
            
            canvas_x_offset = (canvas_w - new_w) // 2
            canvas_y_offset = (canvas_h - new_h) // 2

            box_x1 = max(0, x1 - canvas_x_offset); box_y1 = max(0, y1 - canvas_y_offset)
            box_x2 = min(new_w, x2 - canvas_x_offset); box_y2 = min(new_h, y2 - canvas_y_offset)

            if box_x1 < box_x2 and box_y1 < box_y2:
                real_x1 = int(box_x1 / ratio); real_y1 = int(box_y1 / ratio)
                real_x2 = int(box_x2 / ratio); real_y2 = int(box_y2 / ratio)
                
                self.save_state()
                # << FIX: Crop dilakukan pada transformed_image >>
                self.transformed_image = self.transformed_image.crop((real_x1, real_y1, real_x2, real_y2))
                
                # << FIX: Terapkan kembali penyesuaian slider setelah crop >>
                self.apply_all_adjustments()
                self.display_image()
                self.update_status("Gambar berhasil dipotong.")
            
            self.toggle_crop_mode()

    def show_histogram(self):
        # << BENAR: Histogram harus menampilkan gambar akhir yang diproses (processed_image) >>
        if not self.processed_image: return

        self.update_status("Menampilkan histogram...")
        hist_window = tk.Toplevel(self.root)
        hist_window.title("Histogram Warna")

        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)

        img_to_hist = self.processed_image.copy()
        if img_to_hist.mode not in ['RGB', 'L']:
            img_to_hist = img_to_hist.convert('RGB')
        
        if img_to_hist.mode == 'RGB':
            r, g, b = img_to_hist.split()
            ax.hist(list(r.getdata()), bins=256, color='red', alpha=0.5, label='Red', range=(0, 256))
            ax.hist(list(g.getdata()), bins=256, color='green', alpha=0.5, label='Green', range=(0, 256))
            ax.hist(list(b.getdata()), bins=256, color='blue', alpha=0.5, label='Blue', range=(0, 256))
            ax.legend()
        elif img_to_hist.mode == 'L':
             ax.hist(list(img_to_hist.getdata()), bins=256, color='gray', alpha=0.75, range=(0, 256))

        ax.set_title("Distribusi Warna")
        ax.set_xlim(0, 255)
        
        canvas = FigureCanvasTkAgg(fig, master=hist_window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def apply_filter(self, filter_type):
        if not self.transformed_image: return
        self.save_state()
        
        # Ambil gambar dasar dari transformed_image
        image_to_filter = self.transformed_image.copy()

        if filter_type == "grayscale":
            self.transformed_image = ImageOps.grayscale(image_to_filter)
        
        elif filter_type == "sepia":
            # Filter sepia memerlukan mode Grayscale terlebih dahulu
            sepia_img = ImageOps.grayscale(image_to_filter)
            sepia_palette = []
            r, g, b = (239, 222, 205)
            for i in range(256):
                sepia_palette.extend((int(r*i/255), int(g*i/255), int(b*i/255)))
            sepia_img.putpalette(sepia_palette)
            self.transformed_image = sepia_img.convert("RGB")
        
        elif filter_type == "blur":
            self.transformed_image = image_to_filter.filter(ImageFilter.GaussianBlur(2))
        
        elif filter_type == "sharpen":
            self.transformed_image = image_to_filter.filter(ImageFilter.SHARPEN)
        
        elif filter_type == "edge_enhance":
            self.transformed_image = image_to_filter.filter(ImageFilter.EDGE_ENHANCE_MORE)

        # << TAMBAHKAN BLOK LOGIKA INI >>
        elif filter_type == "invert":
            # Pastikan gambar dalam mode RGB sebelum di-invert untuk hasil terbaik
            if image_to_filter.mode != 'RGB':
                image_to_filter = image_to_filter.convert('RGB')
            self.transformed_image = ImageOps.invert(image_to_filter)

        # Setelah filter diterapkan, panggil dua fungsi ini
        self.apply_all_adjustments()
        self.display_image()
        self.update_status(f"Filter '{filter_type}' diterapkan.")

if __name__ == "__main__":
    root = ThemedTk(theme="arc")
    app = PhotoEditorFinal(root)
    root.mainloop()