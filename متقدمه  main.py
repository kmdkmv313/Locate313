import requests
import socket
import webbrowser
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from ip2geotools.databases.noncommercial import DbIpCity
from geopy.geocoders import Nominatim
import folium
import json
from wifi import Cell, Scheme
import platform
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class AdvancedGeoLocator:
    def __init__(self, master):
        self.master = master
        master.title("أداة تحديد الموقع الجغرافي المتقدمة - v2.0")
        master.geometry("800x600")
        
        # تحذير قانوني
        self.create_warning_frame()
        
        # إنشاء واجهة التبويبات
        self.notebook = ttk.Notebook(master)
        
        # تبويب تحديد الموقع الأساسي
        self.tab_basic = ttk.Frame(self.notebook)
        self.create_basic_tab()
        
        # تبويب الشبكات اللاسلكية
        self.tab_wifi = ttk.Frame(self.notebook)
        self.create_wifi_tab()
        
        # تبويب الإعدادات
        self.tab_settings = ttk.Frame(self.notebook)
        self.create_settings_tab()
        
        self.notebook.add(self.tab_basic, text="تحديد الموقع")
        self.notebook.add(self.tab_wifi, text="الشبكات اللاسلكية")
        self.notebook.add(self.tab_settings, text="الإعدادات")
        self.notebook.pack(expand=True, fill="both")
        
        # متغيرات التطبيق
        self.last_location = None
        self.last_ip = None
        self.settings = {
            "privacy_level": "medium",
            "map_provider": "openstreetmap",
            "save_reports": True,
            "report_folder": "reports"
        }
        self.load_settings()
        
    def create_warning_frame(self):
        """إنشاء إطار التحذير القانوني"""
        warning_frame = tk.Frame(self.master, bg="red", height=50)
        warning_frame.pack(fill="x", side="top")
        
        warning_label = tk.Label(
            warning_frame,
            text="⚠️ تحذير: استخدام هذه الأداة لتحديد مواقع أشخاص دون موافقتهم غير قانوني. للأغراض التعليمية والقانونية فقط ⚠️",
            fg="white",
            bg="red",
            font=('Arial', 10, 'bold'),
            wraplength=750
        )
        warning_label.pack(pady=10)
    
    def create_basic_tab(self):
        """إنشاء واجهة تبويب تحديد الموقع الأساسي"""
        # إطار الإدخال
        input_frame = ttk.LabelFrame(self.tab_basic, text="معلومات الهدف")
        input_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(input_frame, text="عنوان IP / النطاق:").grid(row=0, column=0, padx=5, pady=5)
        self.ip_entry = ttk.Entry(input_frame, width=40)
        self.ip_entry.grid(row=0, column=1, padx=5, pady=5)
        
        self.locate_btn = ttk.Button(input_frame, text="تحديد الموقع", command=self.locate_target)
        self.locate_btn.grid(row=0, column=2, padx=5, pady=5)
        
        self.current_ip_btn = ttk.Button(input_frame, text="موقعي الحالي", command=self.locate_current)
        self.current_ip_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # إطار النتائج
        result_frame = ttk.LabelFrame(self.tab_basic, text="نتائج الموقع")
        result_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(result_frame, height=10, wrap="word")
        self.result_text.pack(fill="both", expand=True, padx=5, pady=5)
        
        # إطار الخريطة
        map_frame = ttk.LabelFrame(self.tab_basic, text="الخريطة")
        map_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.map_btn = ttk.Button(map_frame, text="عرض الخريطة", command=self.show_map, state="disabled")
        self.map_btn.pack(side="left", padx=5, pady=5)
        
        self.save_report_btn = ttk.Button(map_frame, text="حفظ التقرير", command=self.save_report, state="disabled")
        self.save_report_btn.pack(side="left", padx=5, pady=5)
        
        self.export_map_btn = ttk.Button(map_frame, text="تصدير الخريطة", command=self.export_map, state="disabled")
        self.export_map_btn.pack(side="left", padx=5, pady=5)
    
    def create_wifi_tab(self):
        """إنشاء واجهة تبويب الشبكات اللاسلكية"""
        # إطار معلومات الشبكة
        wifi_info_frame = ttk.LabelFrame(self.tab_wifi, text="معلومات الشبكات القريبة")
        wifi_info_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.wifi_tree = ttk.Treeview(wifi_info_frame, columns=("SSID", "BSSID", "Signal", "Channel"), show="headings")
        self.wifi_tree.heading("SSID", text="اسم الشبكة")
        self.wifi_tree.heading("BSSID", text="عنوان MAC")
        self.wifi_tree.heading("Signal", text="قوة الإشارة")
        self.wifi_tree.heading("Channel", text="القناة")
        self.wifi_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        scan_btn = ttk.Button(wifi_info_frame, text="مسح الشبكات", command=self.scan_wifi_networks)
        scan_btn.pack(pady=5)
        
        # إطار تحليل الشبكة
        analysis_frame = ttk.LabelFrame(self.tab_wifi, text="تحليل الشبكة")
        analysis_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.figure = plt.Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, analysis_frame)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        
        analyze_btn = ttk.Button(analysis_frame, text="تحليل الإشارات", command=self.analyze_signals)
        analyze_btn.pack(pady=5)
    
    def create_settings_tab(self):
        """إنشاء واجهة تبويب الإعدادات"""
        # إعدادات الخصوصية
        privacy_frame = ttk.LabelFrame(self.tab_settings, text="إعدادات الخصوصية")
        privacy_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(privacy_frame, text="مستوى الخصوصية:").grid(row=0, column=0, padx=5, pady=5)
        self.privacy_level = tk.StringVar(value=self.settings["privacy_level"])
        privacy_options = ttk.Combobox(privacy_frame, textvariable=self.privacy_level, 
                                     values=["low", "medium", "high"], state="readonly")
        privacy_options.grid(row=0, column=1, padx=5, pady=5)
        
        # إعدادات الخريطة
        map_frame = ttk.LabelFrame(self.tab_settings, text="إعدادات الخريطة")
        map_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(map_frame, text="مزود الخريطة:").grid(row=0, column=0, padx=5, pady=5)
        self.map_provider = tk.StringVar(value=self.settings["map_provider"])
        map_options = ttk.Combobox(map_frame, textvariable=self.map_provider, 
                                  values=["openstreetmap", "google", "mapbox"], state="readonly")
        map_options.grid(row=0, column=1, padx=5, pady=5)
        
        # إعدادات التقارير
        report_frame = ttk.LabelFrame(self.tab_settings, text="إعدادات التقارير")
        report_frame.pack(fill="x", padx=10, pady=5)
        
        self.save_reports = tk.BooleanVar(value=self.settings["save_reports"])
        ttk.Checkbutton(report_frame, text="حفظ التقارير تلقائياً", variable=self.save_reports).grid(row=0, column=0, padx=5, pady=5)
        
        ttk.Label(report_frame, text="مسار حفظ التقارير:").grid(row=1, column=0, padx=5, pady=5)
        self.report_folder = tk.StringVar(value=self.settings["report_folder"])
        ttk.Entry(report_frame, textvariable=self.report_folder, width=30).grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(report_frame, text="استعراض...", command=self.browse_folder).grid(row=1, column=2, padx=5, pady=5)
        
        # زر حفظ الإعدادات
        save_btn = ttk.Button(self.tab_settings, text="حفظ الإعدادات", command=self.save_settings)
        save_btn.pack(pady=10)
    
    def browse_folder(self):
        """اختيار مجلد لحفظ التقارير"""
        folder = filedialog.askdirectory()
        if folder:
            self.report_folder.set(folder)
    
    def load_settings(self):
        """تحميل الإعدادات من ملف"""
        try:
            with open('geolocator_settings.json', 'r') as f:
                self.settings.update(json.load(f))
        except FileNotFoundError:
            pass
    
    def save_settings(self):
        """حفظ الإعدادات في ملف"""
        self.settings.update({
            "privacy_level": self.privacy_level.get(),
            "map_provider": self.map_provider.get(),
            "save_reports": self.save_reports.get(),
            "report_folder": self.report_folder.get()
        })
        
        try:
            with open('geolocator_settings.json', 'w') as f:
                json.dump(self.settings, f)
            messagebox.showinfo("تم", "تم حفظ الإعدادات بنجاح")
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر حفظ الإعدادات: {str(e)}")
    
    def get_public_ip(self):
        """الحصول على عنوان IP العام"""
        try:
            response = requests.get('https://api.ipify.org?format=json', timeout=5)
            return response.json()['ip']
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر الحصول على عنوان IP العام: {str(e)}")
            return None
    
    def get_ip_info(self, ip_or_domain):
        """الحصول على معلومات الموقع من عنوان IP أو النطاق"""
        try:
            # إذا كان نطاق، نحوله إلى IP
            if not ip_or_domain.replace('.', '').isdigit():
                ip_or_domain = socket.gethostbyname(ip_or_domain)
            
            response = DbIpCity.get(ip_or_domain, api_key='free')
            return response
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر تحديد الموقع: {str(e)}")
            return None
    
    def get_address_details(self, latitude, longitude):
        """الحصول على تفاصيل العنوان من الإحداثيات"""
        try:
            geolocator = Nominatim(user_agent="advanced_geo_locator")
            location = geolocator.reverse(f"{latitude}, {longitude}")
            return location.address if location else "تفاصيل العنوان غير متوفرة"
        except Exception as e:
            return f"تعذر الحصول على تفاصيل العنوان: {str(e)}"
    
    def create_map(self, latitude, longitude):
        """إنشاء خريطة HTML باستخدام folium"""
        try:
            if self.map_provider.get() == "openstreetmap":
                m = folium.Map(location=[latitude, longitude], zoom_start=12)
            elif self.map_provider.get() == "google":
                m = folium.Map(
                    location=[latitude, longitude], 
                    zoom_start=12,
                    tiles="https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}",
                    attr="Google"
                )
            else:  # mapbox
                m = folium.Map(
                    location=[latitude, longitude],
                    zoom_start=12,
                    tiles="https://api.mapbox.com/styles/v1/mapbox/streets-v11/tiles/{z}/{x}/{y}?access_token=YOUR_MAPBOX_TOKEN",
                    attr="Mapbox"
                )
            
            folium.Marker(
                [latitude, longitude],
                popup=f"الموقع المقدر: {latitude}, {longitude}",
                icon=folium.Icon(color='red')
            ).add_to(m)
            
            map_file = os.path.join(self.settings["report_folder"], "location_map.html")
            m.save(map_file)
            return map_file
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر إنشاء الخريطة: {str(e)}")
            return None
    
    def locate_target(self):
        """تحديد الموقع بناء على المدخلات"""
        target = self.ip_entry.get().strip()
        if not target:
            messagebox.showerror("خطأ", "الرجاء إدخال عنوان IP أو نطاق")
            return
        
        try:
            self.last_ip = target if target.replace('.', '').isdigit() else socket.gethostbyname(target)
            self.last_location = self.get_ip_info(target)
            
            if not self.last_location:
                return
            
            address = self.get_address_details(self.last_location.latitude, self.last_location.longitude)
            
            info = (
                f"⦿ عنوان IP: {self.last_location.ip_address}\n"
                f"⦿ الدولة: {self.last_location.country}\n"
                f"⦿ المنطقة: {self.last_location.region}\n"
                f"⦿ المدينة: {self.last_location.city}\n"
                f"⦿ الإحداثيات: {self.last_location.latitude}, {self.last_location.longitude}\n"
                f"⦿ المنطقة الزمنية: {self.last_location.time_zone}\n"
                f"⦿ مزود الخدمة: {getattr(self.last_location, 'isp', 'غير معروف')}\n\n"
                f"⦿ العنوان المقدر:\n{address}"
            )
            
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, info)
            
            self.map_btn.config(state="normal")
            self.save_report_btn.config(state="normal")
            self.export_map_btn.config(state="normal")
            
            if self.save_reports.get():
                self.save_report()
                
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تحديد الموقع: {str(e)}")
    
    def locate_current(self):
        """تحديد الموقع الحالي للمستخدم"""
        try:
            current_ip = self.get_public_ip()
            if not current_ip:
                return
            
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, current_ip)
            self.locate_target()
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تحديد الموقع الحالي: {str(e)}")
    
    def show_map(self):
        """عرض الخريطة في المتصفح"""
        if not self.last_location:
            return
        
        map_file = self.create_map(self.last_location.latitude, self.last_location.longitude)
        if map_file:
            webbrowser.open(f"file://{os.path.abspath(map_file)}")
        else:
            messagebox.showerror("خطأ", "تعذر إنشاء الخريطة")
    
    def save_report(self):
        """حفظ التقرير في ملف"""
        if not self.last_location:
            return
        
        try:
            if not os.path.exists(self.settings["report_folder"]):
                os.makedirs(self.settings["report_folder"])
            
            report_file = os.path.join(self.settings["report_folder"], 
                                     f"geo_report_{self.last_ip}_{time.strftime('%Y%m%d_%H%M%S')}.txt")
            
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(self.result_text.get(1.0, tk.END))
            
            messagebox.showinfo("تم", f"تم حفظ التقرير في:\n{report_file}")
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر حفظ التقرير: {str(e)}")
    
    def export_map(self):
        """تصدير الخريطة كصورة"""
        if not self.last_location:
            return
        
        try:
            map_file = self.create_map(self.last_location.latitude, self.last_location.longitude)
            if not map_file:
                return
                
            # هنا يمكن إضافة كود لتحويل HTML إلى صورة باستخدام مكتبات مثل selenium
            messagebox.showinfo("معلومة", "يجب تطوير هذه الوظيفة لتحويل الخريطة HTML إلى صورة")
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر تصدير الخريطة: {str(e)}")
    
    def scan_wifi_networks(self):
        """مسح الشبكات اللاسلكية القريبة"""
        try:
            if platform.system() != "Linux":
                messagebox.showwarning("تحذير", "هذه الميزة تعمل بشكل كامل على أنظمة Linux فقط")
                return
            
            self.wifi_tree.delete(*self.wifi_tree.get_children())
            cells = Cell.all('wlan0')
            
            for cell in cells:
                self.wifi_tree.insert("", "end", values=(
                    cell.ssid,
                    cell.address,
                    cell.signal,
                    cell.channel
                ))
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر مسح الشبكات اللاسلكية: {str(e)}")
    
    def analyze_signals(self):
        """تحليل إشارات الشبكات اللاسلكية"""
        try:
            if platform.system() != "Linux":
                messagebox.showwarning("تحذير", "هذه الميزة تعمل بشكل كامل على أنظمة Linux فقط")
                return
            
            cells = Cell.all('wlan0')
            if not cells:
                messagebox.showinfo("معلومة", "لم يتم العثور على شبكات لاسلكية")
                return
            
            self.ax.clear()
            
            ssids = [cell.ssid if cell.ssid else "مخفي" for cell in cells]
            signals = [cell.signal for cell in cells]
            
            self.ax.barh(ssids, signals, color='skyblue')
            self.ax.set_xlabel('قوة الإشارة (dBm)')
            self.ax.set_title('تحليل قوة إشارات الشبكات اللاسلكية')
            
            self.figure.tight_layout()
            self.canvas.draw()
            
        except Exception as e:
            messagebox.showerror("خطأ", f"تعذر تحليل الإشارات: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedGeoLocator(root)
    root.mainloop()
