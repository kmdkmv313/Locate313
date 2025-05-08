import requests
import json
import socket
import webbrowser
from ip2geotools.databases.noncommercial import DbIpCity
from geopy.geocoders import Nominatim
import folium
import platform
import tkinter as tk
from tkinter import messagebox

class GeoLocatorApp:
    def __init__(self, master):
        self.master = master
        master.title("أداة تحديد الموقع الجغرافي - للاستخدام القانوني فقط")
        
        # تحذير قانوني
        self.label_warning = tk.Label(
            master,
            text="⚠️ تحذير: استخدام هذه الأداة لتحديد مواقع أشخاص دون موافقتهم غير قانوني ⚠️",
            fg="red",
            font=('Arial', 10, 'bold')
        )
        self.label_warning.pack(pady=10)
        
        # واجهة المستخدم
        self.label = tk.Label(master, text="أدخل عنوان IP أو اسم نطاق:")
        self.label.pack()
        
        self.entry = tk.Entry(master, width=40)
        self.entry.pack()
        
        self.button = tk.Button(master, text="تحديد الموقع", command=self.locate)
        self.button.pack(pady=10)
        
        self.result_label = tk.Label(master, text="", wraplength=300)
        self.result_label.pack()
        
        self.map_button = tk.Button(master, text="عرض الخريطة", command=self.show_map, state=tk.DISABLED)
        self.map_button.pack(pady=5)
        
        self.current_ip_button = tk.Button(master, text="تحديد موقعي الحالي", command=self.locate_current)
        self.current_ip_button.pack(pady=5)
        
        # متغيرات لتخزين البيانات
        self.last_location = None
        self.last_ip = None
    
    def get_public_ip(self):
        """الحصول على عنوان IP العام"""
        try:
            response = requests.get('https://api.ipify.org?format=json')
            return response.json()['ip']
        except Exception as e:
            print(f"Error getting public IP: {e}")
            return None
    
    def get_ip_info(self, ip_or_domain):
        """الحصول على معلومات الموقع من عنوان IP أو النطاق"""
        try:
            # إذا كان نطاق، نحوله إلى IP
            if not ip_or_domain.replace('.', '').isdigit():
                ip_or_domain = socket.gethostbyname(ip_or_domain)
            
            response = DbIpCity.get(ip_or_domain, api_key='free')
            self.last_ip = ip_or_domain
            self.last_location = response
            return response
        except Exception as e:
            print(f"Error getting location: {e}")
            return None
    
    def get_address_details(self, latitude, longitude):
        """الحصول على تفاصيل العنوان من الإحداثيات"""
        geolocator = Nominatim(user_agent="geo_locator_app")
        location = geolocator.reverse(f"{latitude}, {longitude}")
        return location.address if location else "تفاصيل العنوان غير متوفرة"
    
    def create_map(self, latitude, longitude):
        """إنشاء خريطة HTML باستخدام folium"""
        try:
            m = folium.Map(location=[latitude, longitude], zoom_start=12)
            folium.Marker(
                [latitude, longitude],
                popup=f"الموقع المقدر: {latitude}, {longitude}",
                icon=folium.Icon(color='red')
            ).add_to(m)
            
            map_file = "location_map.html"
            m.save(map_file)
            return map_file
        except Exception as e:
            print(f"Error creating map: {e}")
            return None
    
    def locate(self):
        """تحديد الموقع بناء على المدخلات"""
        target = self.entry.get().strip()
        if not target:
            messagebox.showerror("خطأ", "الرجاء إدخال عنوان IP أو نطاق")
            return
        
        try:
            result = self.get_ip_info(target)
            if not result:
                messagebox.showerror("خطأ", "تعذر تحديد الموقع. تأكد من صحة المدخلات.")
                return
            
            address = self.get_address_details(result.latitude, result.longitude)
            
            info = (
                f"عنوان IP: {result.ip_address}\n"
                f"الدولة: {result.country}\n"
                f"المدينة: {result.city}\n"
                f"الإحداثيات: {result.latitude}, {result.longitude}\n"
                f"المنطقة الزمنية: {result.time_zone}\n"
                f"مزود الخدمة: {result.isp if hasattr(result, 'isp') else 'غير معروف'}\n"
                f"العنوان المقدر: {address}"
            )
            
            self.result_label.config(text=info)
            self.map_button.config(state=tk.NORMAL)
            self.last_location = result
            
        except Exception as e:
            messagebox.showerror("خطأ", f"حدث خطأ أثناء تحديد الموقع: {str(e)}")
    
    def locate_current(self):
        """تحديد الموقع الحالي للمستخدم"""
        try:
            current_ip = self.get_public_ip()
            if not current_ip:
                messagebox.showerror("خطأ", "تعذر الحصول على عنوان IP الحالي")
                return
            
            self.entry.delete(0, tk.END)
            self.entry.insert(0, current_ip)
            self.locate()
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

if __name__ == "__main__":
    root = tk.Tk()
    app = GeoLocatorApp(root)
    
    # إضافة تذييل
    footer = tk.Label(
        root,
        text="هذه الأداة للأغراض التعليمية والقانونية فقط\n© 2023 - يجب استخدامها بشكل أخلاقي",
        fg="gray",
        font=('Arial', 8)
    )
    footer.pack(pady=10, side=tk.BOTTOM)
    
    root.mainloop()
