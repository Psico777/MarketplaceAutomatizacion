"""
Interfaz Gráfica para Automatización de Facebook Marketplace
Con vista previa de imágenes, selección individual y subida rápida
"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import sys
import json
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from modules.pdf_extractor import PDFImageExtractor
from modules.ai_analyzer import AIImageAnalyzer
from modules.facebook_auth import FacebookAuthenticator
from modules.marketplace_automation import MarketplaceAutomation
from config.settings import Config


class MarketplaceGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Marketplace Automation - LK")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Configuración
        self.config = Config()
        self.pdf_extractor = PDFImageExtractor()
        self.ai_analyzer = AIImageAnalyzer(self.config.GEMINI_API_KEY)
        
        # Estado
        self.current_pdf = None
        self.extracted_images = []
        self.selected_images = []
        self.ai_cache = {}
        self.driver = None
        self.marketplace = None
        
        # Cargar caché de IA
        self.cache_file = "ai_analysis_cache.json"
        self.load_ai_cache()
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configurar interfaz de usuario"""
        # ===== HEADER =====
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="📦 Facebook Marketplace Automation",
            font=("Segoe UI", 24, "bold"),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(pady=20)
        
        # ===== BARRA DE ACCIONES =====
        action_frame = tk.Frame(self.root, bg='#34495e', height=60)
        action_frame.pack(fill=tk.X)
        action_frame.pack_propagate(False)
        
        btn_style = {
            'font': ('Segoe UI', 11, 'bold'),
            'height': 2,
            'relief': tk.FLAT,
            'cursor': 'hand2'
        }
        
        self.btn_load_pdf = tk.Button(
            action_frame,
            text="📄 Cargar PDF",
            bg='#3498db',
            fg='white',
            command=self.load_pdf,
            **btn_style
        )
        self.btn_load_pdf.pack(side=tk.LEFT, padx=10, pady=10, ipadx=10)
        
        self.btn_select_all = tk.Button(
            action_frame,
            text="✓ Seleccionar Todo",
            bg='#2ecc71',
            fg='white',
            command=self.select_all_images,
            state=tk.DISABLED,
            **btn_style
        )
        self.btn_select_all.pack(side=tk.LEFT, padx=5, pady=10, ipadx=10)
        
        self.btn_deselect_all = tk.Button(
            action_frame,
            text="✗ Deseleccionar Todo",
            bg='#e74c3c',
            fg='white',
            command=self.deselect_all_images,
            state=tk.DISABLED,
            **btn_style
        )
        self.btn_deselect_all.pack(side=tk.LEFT, padx=5, pady=10, ipadx=10)
        
        self.btn_login = tk.Button(
            action_frame,
            text="🔐 Login Facebook",
            bg='#9b59b6',
            fg='white',
            command=self.login_facebook,
            **btn_style
        )
        self.btn_login.pack(side=tk.LEFT, padx=5, pady=10, ipadx=10)
        
        self.btn_upload_selected = tk.Button(
            action_frame,
            text="🚀 Subir Seleccionados",
            bg='#e67e22',
            fg='white',
            command=self.upload_selected,
            state=tk.DISABLED,
            **btn_style
        )
        self.btn_upload_selected.pack(side=tk.LEFT, padx=5, pady=10, ipadx=10)
        
        # Status label
        self.status_label = tk.Label(
            action_frame,
            text="Listo - Carga un PDF para comenzar",
            font=('Segoe UI', 10),
            fg='white',
            bg='#34495e'
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)
        
        # ===== CONTENIDO PRINCIPAL =====
        main_frame = tk.Frame(self.root, bg='#ecf0f1')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Panel izquierdo - Vista previa de imágenes
        left_panel = tk.LabelFrame(
            main_frame,
            text="📸 Vista Previa de Imágenes",
            font=('Segoe UI', 12, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        # Scrollable canvas para imágenes
        self.canvas = tk.Canvas(left_panel, bg='white')
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='white')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Panel derecho - Información y progreso
        right_panel = tk.LabelFrame(
            main_frame,
            text="ℹ️ Información y Progreso",
            font=('Segoe UI', 12, 'bold'),
            bg='#ecf0f1',
            fg='#2c3e50',
            width=400
        )
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(5, 0))
        right_panel.pack_propagate(False)
        
        # Info del PDF
        info_frame = tk.Frame(right_panel, bg='white', relief=tk.SOLID, borderwidth=1)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.info_text = tk.Text(
            info_frame,
            height=8,
            font=('Consolas', 10),
            wrap=tk.WORD,
            bg='#f8f9fa',
            fg='#2c3e50',
            relief=tk.FLAT
        )
        self.info_text.pack(fill=tk.BOTH, padx=5, pady=5)
        self.info_text.insert('1.0', "No hay PDF cargado\n\nCarga un PDF para comenzar")
        self.info_text.config(state=tk.DISABLED)
        
        # Progreso
        progress_frame = tk.LabelFrame(
            right_panel,
            text="📊 Progreso de Subida",
            font=('Segoe UI', 11, 'bold'),
            bg='white'
        )
        progress_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=350
        )
        self.progress_bar.pack(padx=10, pady=10)
        
        self.progress_label = tk.Label(
            progress_frame,
            text="0 / 0 productos subidos",
            font=('Segoe UI', 10),
            bg='white'
        )
        self.progress_label.pack(pady=5)
        
        # Log de actividad
        log_frame = tk.LabelFrame(
            right_panel,
            text="📝 Log de Actividad",
            font=('Segoe UI', 11, 'bold'),
            bg='white'
        )
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.log_text = tk.Text(
            log_frame,
            font=('Consolas', 9),
            wrap=tk.WORD,
            bg='#2c3e50',
            fg='#2ecc71',
            relief=tk.FLAT
        )
        log_scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scrollbar.set)
        
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        log_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.log("✓ Sistema iniciado correctamente")
    
    def log(self, message):
        """Agregar mensaje al log"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update_idletasks()
    
    def update_status(self, message):
        """Actualizar barra de estado"""
        self.status_label.config(text=message)
        self.root.update_idletasks()
    
    def load_ai_cache(self):
        """Cargar caché de análisis IA"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.ai_cache = json.load(f)
                self.log(f"✓ Caché cargado: {len(self.ai_cache)} análisis")
            except:
                self.ai_cache = {}
    
    def save_ai_cache(self):
        """Guardar caché de análisis IA"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.ai_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.log(f"⚠ Error guardando caché: {e}")
    
    def load_pdf(self):
        """Cargar y extraer imágenes de PDF"""
        pdf_path = filedialog.askopenfilename(
            title="Seleccionar PDF",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if not pdf_path:
            return
        
        self.current_pdf = pdf_path
        self.update_status("Extrayendo imágenes del PDF...")
        self.log(f"📄 Cargando PDF: {os.path.basename(pdf_path)}")
        
        # Extraer en thread para no bloquear UI
        thread = threading.Thread(target=self._extract_images_thread, args=(pdf_path,))
        thread.start()
    
    def _extract_images_thread(self, pdf_path):
        """Extraer imágenes en thread separado"""
        try:
            self.extracted_images = self.pdf_extractor.extract_images_from_pdf(pdf_path)
            
            if not self.extracted_images:
                self.root.after(0, lambda: messagebox.showerror("Error", "No se pudieron extraer imágenes"))
                return
            
            self.log(f"✓ Extraídas {len(self.extracted_images)} imágenes")
            
            # Actualizar UI en el thread principal
            self.root.after(0, self._display_images)
            self.root.after(0, self._update_info)
            self.root.after(0, lambda: self.update_status(f"Listo - {len(self.extracted_images)} imágenes extraídas"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error extrayendo PDF: {e}"))
            self.log(f"✗ Error: {e}")
    
    def _display_images(self):
        """Mostrar imágenes en grid de 4 columnas"""
        # Limpiar frame anterior
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.selected_images = []
        
        # Crear grid de imágenes (4 columnas)
        for idx, img_path in enumerate(self.extracted_images):
            row = idx // 4
            col = idx % 4
            self._create_image_card(idx, img_path, row, col)
        
        # Habilitar botones
        self.btn_select_all.config(state=tk.NORMAL)
        self.btn_deselect_all.config(state=tk.NORMAL)
    
    def _create_image_card(self, idx, img_path, row, col):
        """Crear tarjeta de imagen con checkbox y preview en grid"""
        page_num = idx + 1
        
        # Frame para cada imagen
        card_frame = tk.Frame(
            self.scrollable_frame,
            bg='white',
            relief=tk.RAISED,
            borderwidth=2,
            width=200,
            height=280
        )
        card_frame.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
        card_frame.grid_propagate(False)
        
        # Configurar peso de columnas para que se expandan
        self.scrollable_frame.grid_columnconfigure(col, weight=1, minsize=200)
        
        # Checkbox
        var = tk.BooleanVar(value=False)
        checkbox = tk.Checkbutton(
            card_frame,
            text=f"Pág. {page_num}",
            variable=var,
            font=('Segoe UI', 10, 'bold'),
            bg='white',
            command=lambda: self._toggle_image(idx, var.get())
        )
        checkbox.pack(anchor=tk.W, padx=5, pady=3)
        
        # Miniatura de imagen (más pequeña para el grid)
        try:
            img = Image.open(img_path)
            img.thumbnail((180, 150))
            photo = ImageTk.PhotoImage(img)
            
            img_label = tk.Label(card_frame, image=photo, bg='white')
            img_label.image = photo  # Mantener referencia
            img_label.pack(pady=3)
        except Exception as e:
            self.log(f"⚠ Error cargando miniatura página {page_num}: {e}")
        
        # Botón de vista previa (más pequeño)
        btn_preview = tk.Button(
            card_frame,
            text="👁️",
            command=lambda: self._show_full_image(img_path, page_num),
            bg='#3498db',
            fg='white',
            font=('Segoe UI', 9),
            relief=tk.FLAT,
            cursor='hand2',
            width=3
        )
        btn_preview.pack(pady=3)
        
        # Guardar referencia
        card_frame.checkbox_var = var
    
    def _toggle_image(self, idx, selected):
        """Toggle selección de imagen"""
        img_path = self.extracted_images[idx]
        if selected:
            if img_path not in self.selected_images:
                self.selected_images.append(img_path)
        else:
            if img_path in self.selected_images:
                self.selected_images.remove(img_path)
        
        self._update_info()
    
    def _show_full_image(self, img_path, page_num):
        """Mostrar imagen completa en ventana nueva"""
        window = tk.Toplevel(self.root)
        window.title(f"Página {page_num}")
        window.geometry("800x600")
        
        try:
            img = Image.open(img_path)
            img.thumbnail((780, 580))
            photo = ImageTk.PhotoImage(img)
            
            label = tk.Label(window, image=photo)
            label.image = photo
            label.pack(padx=10, pady=10)
        except Exception as e:
            tk.Label(window, text=f"Error cargando imagen: {e}").pack()
    
    def _update_info(self):
        """Actualizar panel de información"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete('1.0', tk.END)
        
        if self.current_pdf:
            pdf_name = os.path.basename(self.current_pdf)
            total = len(self.extracted_images)
            selected = len(self.selected_images)
            
            info = f"""PDF Cargado:
{pdf_name}

Total de páginas: {total}
Páginas seleccionadas: {selected}

Estado: {"Listo para subir" if selected > 0 else "Sin selección"}
"""
            self.info_text.insert('1.0', info)
        
        self.info_text.config(state=tk.DISABLED)
        
        # Habilitar botón de subida si hay seleccionados y está logueado
        if len(self.selected_images) > 0 and self.driver:
            self.btn_upload_selected.config(state=tk.NORMAL)
        else:
            self.btn_upload_selected.config(state=tk.DISABLED)
    
    def select_all_images(self):
        """Seleccionar todas las imágenes"""
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'checkbox_var'):
                widget.checkbox_var.set(True)
        
        self.selected_images = self.extracted_images.copy()
        self._update_info()
        self.log(f"✓ Todas las imágenes seleccionadas ({len(self.selected_images)})")
    
    def deselect_all_images(self):
        """Deseleccionar todas las imágenes"""
        for widget in self.scrollable_frame.winfo_children():
            if hasattr(widget, 'checkbox_var'):
                widget.checkbox_var.set(False)
        
        self.selected_images = []
        self._update_info()
        self.log("✓ Todas las imágenes deseleccionadas")
    
    def login_facebook(self):
        """Login a Facebook"""
        if self.driver:
            messagebox.showinfo("Info", "Ya hay una sesión activa")
            return
        
        self.update_status("Iniciando sesión en Facebook...")
        self.log("🔐 Iniciando login...")
        self.btn_login.config(state=tk.DISABLED)
        
        thread = threading.Thread(target=self._login_thread)
        thread.start()
    
    def _twofa_callback(self):
        """Callback para confirmar 2FA desde la GUI"""
        self.twofa_confirmed = False
        
        def on_confirm():
            self.twofa_confirmed = True
            dialog.destroy()
        
        # Crear diálogo modal
        dialog = tk.Toplevel(self.root)
        dialog.title("Confirmación 2FA")
        dialog.geometry("450x280")
        dialog.resizable(False, False)
        dialog.configure(bg='#2c3e50')
        
        # Centrar en pantalla
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Contenido
        tk.Label(
            dialog,
            text="🔐 2FA Requerido",
            font=('Segoe UI', 16, 'bold'),
            fg='white',
            bg='#2c3e50'
        ).pack(pady=20)
        
        msg = """Aprueba el inicio de sesión en tu celular

1. Revisa notificación de Facebook
2. Aprueba el login
3. Espera a ver tu feed de Facebook
4. Click en el botón de abajo"""
        
        tk.Label(
            dialog,
            text=msg,
            font=('Segoe UI', 11),
            fg='white',
            bg='#2c3e50',
            justify=tk.LEFT
        ).pack(pady=10)
        
        btn = tk.Button(
            dialog,
            text="✓ Ya aprobé en mi celular",
            command=on_confirm,
            bg='#2ecc71',
            fg='white',
            font=('Segoe UI', 12, 'bold'),
            height=2,
            cursor='hand2'
        )
        btn.pack(pady=20, padx=40, fill=tk.X)
        
        # Esperar a que el usuario confirme
        self.root.wait_window(dialog)
        
        # Retornar True si se confirmó (importante para facebook_auth.py)
        return self.twofa_confirmed
    
    def _login_thread(self):
        """Login en thread separado"""
        try:
            auth = FacebookAuthenticator(
                email=self.config.FACEBOOK_EMAIL,
                password=self.config.FACEBOOK_PASSWORD,
                two_fa_secret=self.config.FACEBOOK_2FA_SECRET,
                headless=self.config.HEADLESS,
                implicit_wait=self.config.IMPLICIT_WAIT,
                twofa_callback=self._twofa_callback
            )
            
            self.driver = auth.login()
            
            if self.driver:
                self.marketplace = MarketplaceAutomation(self.driver)
                self.root.after(0, lambda: self.log("✓ Login exitoso"))
                self.root.after(0, lambda: self.update_status("Conectado - Listo para subir"))
                self.root.after(0, lambda: self._update_info())
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", "Login fallido"))
                self.root.after(0, lambda: self.btn_login.config(state=tk.NORMAL))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Error en login: {e}"))
            self.root.after(0, lambda: self.btn_login.config(state=tk.NORMAL))
    
    def upload_selected(self):
        """Subir productos seleccionados"""
        if not self.selected_images:
            messagebox.showwarning("Advertencia", "No hay imágenes seleccionadas")
            return
        
        if not self.driver or not self.marketplace:
            messagebox.showerror("Error", "Debes hacer login primero")
            return
        
        # Confirmar
        response = messagebox.askyesno(
            "Confirmar",
            f"¿Subir {len(self.selected_images)} productos a Facebook Marketplace?"
        )
        
        if not response:
            return
        
        self.btn_upload_selected.config(state=tk.DISABLED)
        self.update_status("Subiendo productos...")
        
        thread = threading.Thread(target=self._upload_thread)
        thread.start()
    
    def _upload_thread(self):
        """Subir productos en thread separado"""
        total = len(self.selected_images)
        success_count = 0
        failed_count = 0
        
        self.root.after(0, lambda: self.progress_bar.config(maximum=total, value=0))
        
        for idx, img_path in enumerate(self.selected_images, 1):
            page_num = self.extracted_images.index(img_path) + 1
            
            self.root.after(0, lambda p=page_num: self.log(f"\n📦 Procesando página {p}..."))
            
            try:
                # Analizar con IA (con caché)
                cache_key = os.path.basename(img_path)
                
                if cache_key in self.ai_cache:
                    self.root.after(0, lambda: self.log("  ⚡ Usando análisis cacheado"))
                    product_info = self.ai_cache[cache_key]
                else:
                    self.root.after(0, lambda: self.log("  🤖 Analizando con IA..."))
                    product_info = self.ai_analyzer.analyze_image_for_marketplace(img_path)
                    self.ai_cache[cache_key] = product_info
                    self.save_ai_cache()
                
                self.root.after(0, lambda t=product_info['title']: self.log(f"  ✓ {t}"))
                
                # Crear listing
                self.root.after(0, lambda: self.log("  🚀 Creando listing..."))
                success = self.marketplace.create_listing(
                    title=product_info['title'],
                    price=product_info['price'],
                    description=product_info['description'],
                    category="Electronics",
                    condition="Nuevo",
                    images=[img_path],
                    tags=product_info['tags']
                )
                
                if success:
                    success_count += 1
                    self.root.after(0, lambda: self.log("  ✓ ÉXITO"))
                else:
                    failed_count += 1
                    self.root.after(0, lambda: self.log("  ✗ FALLÓ"))
                
            except Exception as e:
                failed_count += 1
                self.root.after(0, lambda e=e: self.log(f"  ✗ Error: {e}"))
            
            # Actualizar progreso
            self.root.after(0, lambda v=idx: self.progress_bar.config(value=v))
            self.root.after(0, lambda s=success_count, f=failed_count, t=total: 
                          self.progress_label.config(text=f"{s} exitosos, {f} fallidos de {t}"))
        
        # Finalizar
        self.root.after(0, lambda: self.log(f"\n✓ Proceso completado: {success_count} éxitos, {failed_count} fallos"))
        self.root.after(0, lambda: self.update_status("Proceso completado"))
        self.root.after(0, lambda: messagebox.showinfo("Completado", 
                                                        f"Subida finalizada\n\n✓ Éxitos: {success_count}\n✗ Fallos: {failed_count}"))
        self.root.after(0, lambda: self.btn_upload_selected.config(state=tk.NORMAL))


def main():
    root = tk.Tk()
    app = MarketplaceGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
