# ==============================================================================
# 🛠️ AYARLAR VE SABİTLER (CONFIG) - V 83.0
# ==============================================================================

DEFAULT_PERSONAS = [
    {"TR": "Su Şartlandırma Kimyasalları ve Sistemleri Baş Mühendisi", "EN": "Head Engineer of Water Treatment Chemicals", "RU": "Главный инженер по водоподготовке", "AR": "كبير مهندسي معالجة المياه"},
    {"TR": "Su Şartlandırma Sistemleri Uzmanı", "EN": "Water Treatment Systems Expert", "RU": "Эксперт по системам водоподготовки", "AR": "خبير أنظمة معالجة المياه"}
]

LANGUAGES = {
    "TR": {
        "name": "Turkish",
        "btn_social_main": "📱 Sosyal Medya Yönetimi", 
        "btn_linkedin": "🔹 LinkedIn",
        "btn_instagram": "📸 Instagram",
        "btn_quote": "💼 Teklif Oluştur",
        "btn_bimaks_tech": "🧪 BİMAKS TEKNİK", 
        
        "nav_analysis": "Sistem Analizi",
        "nav_roi": "ROI (Yatırım Geri Dönüşü)",
        "nav_ocr": "Analizden Sistem Yorumlama",
        "nav_reg": "Global Mevzuat",
        
        "solver_title": "Sistem Analizi ve LSI Hesaplama",
        "solver_ph": "Mevcut problemi detaylıca anlatın (Örn: Eşanjörlerde aşırı kireçlenme, korozyon vb...)",
        "mk_water": "🧪 Makeup (Besleme) Suyu",
        "sy_water": "⚗️ Sistem (Kule/Kazan) Suyu",
        "btn_analyze": "🚀 ANALİZ ET VE ÇÖZÜM ÜRET",
        "lsi_result": "📊 LSI / RSI Endeks Sonuçları",
        "lsi_info": "ℹ️ DİKKAT: LSI/RSI otomatik hesabı için pH, TDS, Sıcaklık, Ca Sertliği ve Alkalinite değerlerinin girilmesi ZORUNLUDUR.",
        
        # Su Analiz Parametreleri
        "ph_req": "pH (Zorunlu)",
        "tds_req": "TDS (ppm) (Zorunlu)",
        "temp_req": "Sıcaklık (°C) (Zorunlu)",
        "ca_req": "Ca Sertliği (Zorunlu)",
        "alk_req": "Alkalinite (Zorunlu)",
        "cond_opt": "İletkenlik",
        "cl_opt": "Klorür",
        "so4_opt": "Sülfat",
        "fe_opt": "Demir",
        "sio2_opt": "Silika",
        
        "roi_title": "Akıllı Dozaj ve Yatırım Geri Dönüşü (ROI) Hesaplayıcı",
        "roi_subtitle_inputs": "⚙️ Mevcut İşletme Verileri",
        "roi_subtitle_costs": "💰 Birim Maliyetler",
        "roi_subtitle_bimaks": "🧪 Bimaks Hedefleri",
        
        "roi_vol": "Sistem Hacmi (m³)",
        "roi_blowdown": "Mevcut Blöf Oranı (m³/saat)",
        "roi_hours": "Yıllık Çalışma Saati",
        "roi_coc_curr": "Mevcut Konsantrasyon Sayısı (CoC)",
        "roi_scale": "Tahmini Kireç Kalınlığı (mm)",
        
        "roi_cost_water": "Su Birim Maliyeti (€/m³)",
        "roi_cost_energy": "Yıllık Toplam Enerji Faturası (€)",
        "roi_cost_chem": "Yıllık Kimyasal Maliyeti (€)",
        
        "roi_coc_target": "Hedeflenen CoC (Bimaks İle)",
        "roi_dose": "Önerilen Dozaj (ppm)",
        "roi_price": "Ürün Birim Fiyatı (€/kg)",
        
        "roi_calc_btn": "📊 DETAYLI ROI ANALİZİ OLUŞTUR",
        
        "tbl_param": "Parametre",
        "tbl_curr": "Mevcut Durum",
        "tbl_bimaks": "Bimaks Çözümü",
        "tbl_save": "Fark / Kazanç",
        "row_water": "Yıllık Su Tüketimi (m³)",
        "row_energy": "Enerji Gideri (€)",
        "row_chem": "Kimyasal Gideri (€)",
        "row_total": "TOPLAM MALİYET (€)",
        
        "ocr_title": "Analizden Sistem Yorumlama (OCR)",
        "ocr_desc": "Müşteriden aldığınız analiz raporunun fotoğrafını yükleyin, yapay zeka okusun ve yorumlasın.",
        "ocr_btn": "📷 RAPORU TARA VE YORUMLA",
        
        "reg_title": "Global Mevzuat ve Sertifikasyon Rehberi",
        "reg_ph": "Örn: Almanya'da fosfonat kullanımı kısıtlamaları nelerdir?",
        
        "sys_select": "Uzmanlık / Rol Seçiniz:", "sys_manual": "🔹 Yeni / Manuel Rol Girişi", 
        "sys_placeholder_select": "--- Rol Seçiniz ---", "topic": "İçerik Konusu / Başlık:", 
        "target_audience": "Hedef Kitle:", "target_def": "Genel Okuyucu",
        "target_plat": "Yayınlanacak Platform:", "plat_def": "LinkedIn",
        "prod_ref": "Tanıtılacak Ürün/Hizmet (Opsiyonel):", "prod_link_lbl": "Ürün/Hizmet Linki (Opsiyonel):",
        "detail_info": "Detaylı Bilgi / Başvuru:", "btn_create": "Profesyonel Makale Oluştur",
        "settings": "⚙️ Ayarlar", 
        "visual": "🖼️ Medya Yükleme (Resim/Video)", "visual_desc": "Görsel yükleyerek içeriğinizi zenginleştirin.", 
        "publish": "LİNKEDİN'DE YAYINLA", "publish_insta": "INSTAGRAM'DA YAYINLA",
        "prompt_limit": "Maksimum karakter:", "guide_btn": "❓ Anahtarlar Nasıl Alınır? (Rehber)",
        "back_btn": "🔙 Uygulamaya Dön", 
        
        "guide_title_main": "🔑 API Anahtarları Alma Rehberi",
        "guide_gemini_title": "1. Google Gemini API (Ücretsiz)", 
        "guide_gemini_text": "**Adım 1:** [Google AI Studio](https://aistudio.google.com/) web sitesine gidin ve Google hesabınızla giriş yapın.\n**Adım 2:** Sol menüde bulunan **'Get API key'** butonuna tıklayın.\n**Adım 3:** Açılan sayfada **'Create API Key'** butonuna basın.\n**Adım 4:** Oluşturulan ve 'AIza' ile başlayan anahtarı kopyalayın.\n**Adım 5:** Bu uygulamada Ayarlar kısmındaki ilgili kutucuğa yapıştırın.",
        "guide_linkedin_title": "2. LinkedIn Access Token", 
        "guide_linkedin_text": "**Adım 1:** [LinkedIn Developers](https://www.linkedin.com/developers/) sayfasına gidin ve 'Create App' diyerek bir uygulama oluşturun.\n**Adım 2:** Uygulama sayfasında 'Products' sekmesine gidin ve **'Share on LinkedIn'** ürününü seçip 'Request Access' deyin.\n**Adım 3:** 'Auth' sekmesinde OAuth 2.0 ayarlarını göreceksiniz.\n**Adım 4:** 'Tools' menüsünden **'Token Generator'** aracını açın.\n**Adım 5:** Scopes (İzinler) kısmında **'openid', 'profile', 'w_member_social'** seçeneklerini işaretleyip Token oluşturun.",
        "guide_instagram_title": "3. Instagram Token & Business ID",
        "guide_instagram_text": "**Adım 1:** [Meta for Developers](https://developers.facebook.com/) adresinden bir işletme uygulaması oluşturun.\n**Adım 2:** 'Instagram Graph API' ürününü uygulamaya ekleyin.\n**Adım 3:** 'Tools' -> **'Graph API Explorer'** aracını açın.\n**Adım 4:** İzinler kısmına **'instagram_basic', 'instagram_content_publish'** ekleyin ve Token oluşturun.\n**Adım 5:** Business ID'nizi yine bu panelden sorgulayarak (me?fields=accounts) bulun.",

        "step1_linkedin_title": "📋 İçerik Detayları (Giriş Yapmak İçin Tıklayın)",
        "settings_title": "⚙️ Uygulama Ayarları",
        "quote_title": "💼 Profesyonel Teklif Oluşturucu",
        "q_invoice_info": "Fatura Ünvanı / Müşteri:", "q_shipping_addr": "Sevk Adresi (Teslimat):",
        "q_period": "Teklif Dönemi / Geçerlilik:", "q_payment": "Ödeme Vadesi:",
        "q_bank_lbl": "Banka Bilgileri:",
        "q_bank_def": "Türkiye Vakıflar Bankası T.A.O. TR12 0001 5001 5800 7299 3551 65",
        "q_prod_name": "Ürün / Hizmet Adı", "q_packaging": "Ambalaj Tipi", "q_shipping_opt": "Nakliye",
        "q_price": "Birim Fiyat", "q_qty": "Miktar", "q_unit": "Birim (kg/adt)", "q_line_total": "Tutar",
        "q_add": "Listeye Ekle", "q_clear": "Temizle", "q_create": "💾 TEKLİFİ İNDİR (PDF)",
        "q_inc": "Dahil", "q_exc": "Hariç", "q_total": "GENEL TOPLAM", "q_show_total": "Genel Toplamı Göster",
        "q_intro": "Ürün ve hizmetlerimizle ilgili teklifimiz tarafınıza aşağıdaki şekilde sunulmuştur:",
        "q_del_item": "Sil", "q_date": "Tarih", "q_note_label": "Teklif Altı Not / Özel Şartlar:", "q_note_ph": "Örn: Ödeme %50 Peşin...",
        "editor": "📝 İçerik Editörü", "role_active": "Aktif Rol", "char_count": "Karakter Sayısı:",
        "set_logo": "Uygulama Logosu Değiştir", "set_logo_btn": "Logo Yükle", "set_role_mgmt": "Rol Yönetimi",
        "set_add_role": "Yeni Rol Ekle", "set_del_role": "Rol Sil", "set_theme": "Görünüm & Tema",
        "set_api_keys": "🔑 API Anahtarları", "set_save": "Kaydet (Genel)", "set_admin": "🔐 Admin & Modül Yönetimi",
        "set_modules": "Modüller", "set_bg": "Arka Plan", "set_txt": "Yazı Rengi", "set_btn": "Buton Rengi"
    },
    "EN": {
        "name": "English",
        "btn_social_main": "📱 Social Media Management", 
        "btn_linkedin": "🔹 LinkedIn",
        "btn_instagram": "📸 Instagram",
        "btn_quote": "💼 Create Quote",
        "btn_bimaks_tech": "🧪 BIMAKS TECH", 
        
        "nav_analysis": "System Analysis",
        "nav_roi": "ROI Calculator",
        "nav_ocr": "OCR & System Interpretation",
        "nav_reg": "Global Regulations",
        
        "solver_title": "System Analysis & LSI Calculator",
        "solver_ph": "Describe the current problem in detail (e.g., excessive scaling in heat exchangers, corrosion...)",
        "mk_water": "🧪 Makeup Water",
        "sy_water": "⚗️ System Water",
        "btn_analyze": "🚀 ANALYZE AND GENERATE SOLUTION",
        "lsi_result": "📊 LSI / RSI Index Results",
        "lsi_info": "ℹ️ ATTENTION: pH, TDS, Temperature, Ca Hardness, and Alkalinity values are MANDATORY for automatic LSI/RSI calculation.",
        
        # Water Analysis Parameters
        "ph_req": "pH (Required)",
        "tds_req": "TDS (ppm) (Required)",
        "temp_req": "Temperature (°C) (Required)",
        "ca_req": "Ca Hardness (Required)",
        "alk_req": "Alkalinity (Required)",
        "cond_opt": "Conductivity",
        "cl_opt": "Chloride",
        "so4_opt": "Sulfate",
        "fe_opt": "Iron",
        "sio2_opt": "Silica",
        
        "roi_title": "Smart Dosage & Return on Investment (ROI) Calculator",
        "roi_subtitle_inputs": "⚙️ Current Operating Data",
        "roi_subtitle_costs": "💰 Unit Costs",
        "roi_subtitle_bimaks": "🧪 Bimaks Targets",
        
        "roi_vol": "System Volume (m³)",
        "roi_blowdown": "Current Blowdown Rate (m³/h)",
        "roi_hours": "Annual Operating Hours",
        "roi_coc_curr": "Current Cycles of Concentration (CoC)",
        "roi_scale": "Estimated Scale Thickness (mm)",
        
        "roi_cost_water": "Water Unit Cost (€/m³)",
        "roi_cost_energy": "Total Annual Energy Bill (€)",
        "roi_cost_chem": "Annual Chemical Cost (€)",
        
        "roi_coc_target": "Target CoC (With Bimaks)",
        "roi_dose": "Recommended Dosage (ppm)",
        "roi_price": "Product Unit Price (€/kg)",
        
        "roi_calc_btn": "📊 GENERATE DETAILED ROI ANALYSIS",
        
        "tbl_param": "Parameter",
        "tbl_curr": "Current Status",
        "tbl_bimaks": "Bimaks Solution",
        "tbl_save": "Difference / Savings",
        "row_water": "Annual Water Consumption (m³)",
        "row_energy": "Energy Cost (€)",
        "row_chem": "Chemical Cost (€)",
        "row_total": "TOTAL COST (€)",
        
        "ocr_title": "OCR System Interpretation",
        "ocr_desc": "Upload a photo of the analysis report you received from the customer, let AI read and interpret it.",
        "ocr_btn": "📷 SCAN AND INTERPRET REPORT",
        
        "reg_title": "Global Regulation and Certification Guide",
        "reg_ph": "e.g., What are the restrictions on phosphonate use in Germany?",
        
        "sys_select": "Select Expertise / Role:", "sys_manual": "🔹 New / Manual Role Entry", 
        "sys_placeholder_select": "--- Select Role ---", "topic": "Content Topic / Title:", 
        "target_audience": "Target Audience:", "target_def": "General Reader",
        "target_plat": "Target Platform:", "plat_def": "LinkedIn",
        "prod_ref": "Product/Service to Promote (Optional):", "prod_link_lbl": "Product/Service Link (Optional):",
        "detail_info": "Detailed Info / Apply:", "btn_create": "Generate Professional Article",
        "settings": "⚙️ Settings", 
        "visual": "🖼️ Media Upload (Image/Video)", "visual_desc": "Enrich your content by uploading visuals.", 
        "publish": "PUBLISH ON LINKEDIN", "publish_insta": "PUBLISH ON INSTAGRAM",
        "prompt_limit": "Max characters:", "guide_btn": "❓ How to Get API Keys? (Guide)",
        "back_btn": "🔙 Back to App", 
        
        "guide_title_main": "🔑 API Key Generation Guide",
        "guide_gemini_title": "1. Google Gemini API (Free)", 
        "guide_gemini_text": "**Step 1:** Go to [Google AI Studio](https://aistudio.google.com/) and log in with your Google account.\n**Step 2:** Click the **'Get API key'** button on the left menu.\n**Step 3:** Click the **'Create API Key'** button on the page that opens.\n**Step 4:** Copy the generated key starting with 'AIza'.\n**Step 5:** Paste it into the relevant box in the Settings section of this app.",
        "guide_linkedin_title": "2. LinkedIn Access Token", 
        "guide_linkedin_text": "**Step 1:** Go to the [LinkedIn Developers](https://www.linkedin.com/developers/) page and create an app by clicking 'Create App'.\n**Step 2:** Go to the 'Products' tab on the app page, select the **'Share on LinkedIn'** product and click 'Request Access'.\n**Step 3:** You will see the OAuth 2.0 settings in the 'Auth' tab.\n**Step 4:** Open the **'Token Generator'** tool from the 'Tools' menu.\n**Step 5:** Select the **'openid', 'profile', 'w_member_social'** options in the Scopes section and generate the Token.",
        "guide_instagram_title": "3. Instagram Token & Business ID",
        "guide_instagram_text": "**Step 1:** Create a business app at [Meta for Developers](https://developers.facebook.com/).\n**Step 2:** Add the 'Instagram Graph API' product to the app.\n**Step 3:** Open the 'Tools' -> **'Graph API Explorer'** tool.\n**Step 4:** Add **'instagram_basic', 'instagram_content_publish'** to the permissions section and generate a Token.\n**Step 5:** Find your Business ID by querying (me?fields=accounts) from this panel.",

        "step1_linkedin_title": "📋 Content Details (Click to Expand)",
        "settings_title": "⚙️ Application Settings",
        "quote_title": "💼 Professional Quote Generator",
        "q_invoice_info": "Invoice Title / Customer:", "q_shipping_addr": "Shipping Address (Delivery):",
        "q_period": "Quote Period / Validity:", "q_payment": "Payment Terms:",
        "q_bank_lbl": "Bank Information:",
        "q_bank_def": "Vakifbank T.A.O. TR12 0001 5001 5800 7299 3551 65",
        "q_prod_name": "Product / Service Name", "q_packaging": "Packaging Type", "q_shipping_opt": "Shipping",
        "q_price": "Unit Price", "q_qty": "Quantity", "q_unit": "Unit (kg/pcs)", "q_line_total": "Amount",
        "q_add": "Add to List", "q_clear": "Clear", "q_create": "💾 DOWNLOAD QUOTE (PDF)",
        "q_inc": "Included", "q_exc": "Excluded", "q_total": "GRAND TOTAL", "q_show_total": "Show Grand Total",
        "q_intro": "Our offer regarding our products and services is presented to you as follows:",
        "q_del_item": "Del", "q_date": "Date", "q_note_label": "Bottom Note / Special Conditions:", "q_note_ph": "e.g., 50% Advance Payment...",
        "editor": "📝 Content Editor", "role_active": "Active Role", "char_count": "Character Count:",
        "set_logo": "Change App Logo", "set_logo_btn": "Upload Logo", "set_role_mgmt": "Role Management",
        "set_add_role": "Add New Role", "set_del_role": "Delete Role", "set_theme": "Appearance & Theme",
        "set_api_keys": "🔑 API Keys", "set_save": "Save (General)", "set_admin": "🔐 Admin & Module Management",
        "set_modules": "Modules", "set_bg": "Background", "set_txt": "Text Color", "set_btn": "Button Color"
    },
    "RU": {
        "name": "Russian",
        "btn_social_main": "📱 Управление соцсетями", 
        "btn_linkedin": "🔹 LinkedIn",
        "btn_instagram": "📸 Instagram",
        "btn_quote": "💼 Создать предложение",
        "btn_bimaks_tech": "🧪 BIMAKS ТЕХНИЧЕСКИЙ", 
        
        "nav_analysis": "Анализ системы",
        "nav_roi": "Калькулятор ROI",
        "nav_ocr": "OCR и анализ отчетов",
        "nav_reg": "Глобальные нормативы",
        
        "solver_title": "Анализ системы и расчет LSI",
        "solver_ph": "Подробно опишите текущую проблему (например, чрезмерное образование накипи в теплообменниках, коррозия...)",
        "mk_water": "🧪 Подпиточная вода",
        "sy_water": "⚗️ Системная вода",
        "btn_analyze": "🚀 ПРОАНАЛИЗИРОВАТЬ И ПРЕДЛОЖИТЬ РЕШЕНИЕ",
        "lsi_result": "📊 Результаты индексов LSI / RSI",
        "lsi_info": "ℹ️ ВНИМАНИЕ: Для автоматического расчета LSI/RSI ОБЯЗАТЕЛЬНО укажите значения pH, TDS, температуры, кальциевой жесткости и щелочности.",
        
        # Water Analysis Parameters
        "ph_req": "pH (Обязательно)",
        "tds_req": "TDS (ppm) (Обязательно)",
        "temp_req": "Темп. (°C) (Обязательно)",
        "ca_req": "Ca Жесткость (Обязательно)",
        "alk_req": "Щелочность (Обязательно)",
        "cond_opt": "Проводимость",
        "cl_opt": "Хлорид",
        "so4_opt": "Сульфат",
        "fe_opt": "Железо",
        "sio2_opt": "Кремнезем",
        
        "roi_title": "Умная дозировка и калькулятор возврата инвестиций (ROI)",
        "roi_subtitle_inputs": "⚙️ Текущие эксплуатационные данные",
        "roi_subtitle_costs": "💰 Удельные затраты",
        "roi_subtitle_bimaks": "🧪 Цели Bimaks",
        
        "roi_vol": "Объем системы (м³)",
        "roi_blowdown": "Текущая продувка (м³/ч)",
        "roi_hours": "Часы работы в год",
        "roi_coc_curr": "Текущий коэффициент концентрирования (CoC)",
        "roi_scale": "Расчетная толщина накипи (мм)",
        
        "roi_cost_water": "Стоимость воды (€/м³)",
        "roi_cost_energy": "Общий годовой счет за энергию (€)",
        "roi_cost_chem": "Годовые затраты на химикаты (€)",
        
        "roi_coc_target": "Целевой CoC (с Bimaks)",
        "roi_dose": "Рекомендуемая дозировка (ppm)",
        "roi_price": "Цена за единицу продукта (€/кг)",
        
        "roi_calc_btn": "📊 СОЗДАТЬ ПОДРОБНЫЙ АНАЛИЗ ROI",
        
        "tbl_param": "Параметр",
        "tbl_curr": "Текущий статус",
        "tbl_bimaks": "Решение Bimaks",
        "tbl_save": "Разница / Экономия",
        "row_water": "Годовое потребление воды (м³)",
        "row_energy": "Затраты на энергию (€)",
        "row_chem": "Затраты на химикаты (€)",
        "row_total": "ОБЩАЯ СТОИМОСТЬ (€)",
        
        "ocr_title": "Интерпретация системы OCR",
        "ocr_desc": "Загрузите фото отчета об анализе, полученного от клиента, и позвольте ИИ прочитать и интерпретировать его.",
        "ocr_btn": "📷 СКАНИРОВАТЬ И ИНТЕРПРЕТИРОВАТЬ",
        
        "reg_title": "Руководство по глобальным нормативам и сертификации",
        "reg_ph": "Например, каковы ограничения на использование фосфонатов в Германии?",
        
        "sys_select": "Выберите специализацию / роль:", "sys_manual": "🔹 Ввод новой/пользовательской роли", 
        "sys_placeholder_select": "--- Выберите роль ---", "topic": "Тема контента / Заголовок:", 
        "target_audience": "Целевая аудитория:", "target_def": "Широкий круг читателей",
        "target_plat": "Целевая платформа:", "plat_def": "LinkedIn",
        "prod_ref": "Продвигаемый продукт/услуга (необязательно):", "prod_link_lbl": "Ссылка на продукт (необязательно):",
        "detail_info": "Подробная информация / Подать заявку:", "btn_create": "Создать профессиональную статью",
        "settings": "⚙️ Настройки", 
        "visual": "🖼️ Загрузка медиа (Изображение/Видео)", "visual_desc": "Обогатите свой контент визуальными эффектами.", 
        "publish": "ОПУБЛИКОВАТЬ В LINKEDIN", "publish_insta": "ОПУБЛИКОВАТЬ В INSTAGRAM",
        "prompt_limit": "Макс. символов:", "guide_btn": "❓ Как получить ключи API? (Руководство)",
        "back_btn": "🔙 Вернуться в приложение", 
        
        "guide_title_main": "🔑 Руководство по получению ключей API",
        "guide_gemini_title": "1. Google Gemini API (Бесплатно)", 
        "guide_gemini_text": "**Шаг 1:** Перейдите на сайт [Google AI Studio](https://aistudio.google.com/) и войдите с помощью Google.\n**Шаг 2:** Нажмите **'Get API key'** в левом меню.\n**Шаг 3:** Нажмите **'Create API Key'**.\n**Шаг 4:** Скопируйте ключ, начинающийся с 'AIza'.\n**Шаг 5:** Вставьте его в соответствующее поле в настройках приложения.",
        "guide_linkedin_title": "2. Токен доступа LinkedIn", 
        "guide_linkedin_text": "**Шаг 1:** Перейдите в [LinkedIn Developers](https://www.linkedin.com/developers/) и создайте приложение (Create App).\n**Шаг 2:** На вкладке 'Products' выберите **'Share on LinkedIn'** и нажмите 'Request Access'.\n**Шаг 3:** Проверьте вкладку 'Auth' для OAuth 2.0.\n**Шаг 4:** Откройте **'Token Generator'** в меню 'Tools'.\n**Шаг 5:** Выберите **'openid', 'profile', 'w_member_social'** и сгенерируйте токен.",
        "guide_instagram_title": "3. Токен Instagram и Business ID",
        "guide_instagram_text": "**Шаг 1:** Создайте приложение на [Meta for Developers](https://developers.facebook.com/).\n**Шаг 2:** Добавьте 'Instagram Graph API'.\n**Шаг 3:** Откройте 'Tools' -> **'Graph API Explorer'**.\n**Шаг 4:** Добавьте **'instagram_basic', 'instagram_content_publish'** и сгенерируйте токен.\n**Шаг 5:** Найдите Business ID через запрос (me?fields=accounts).",

        "step1_linkedin_title": "📋 Детали контента (Нажмите, чтобы развернуть)",
        "settings_title": "⚙️ Настройки приложения",
        "quote_title": "💼 Профессиональный генератор предложений",
        "q_invoice_info": "Название счета / Клиент:", "q_shipping_addr": "Адрес доставки:",
        "q_period": "Срок действия:", "q_payment": "Условия оплаты:",
        "q_bank_lbl": "Банковские реквизиты:",
        "q_bank_def": "Vakifbank T.A.O. TR12 0001 5001 5800 7299 3551 65",
        "q_prod_name": "Название продукта / услуги", "q_packaging": "Тип упаковки", "q_shipping_opt": "Доставка",
        "q_price": "Цена за ед.", "q_qty": "Количество", "q_unit": "Ед. изм. (кг/шт)", "q_line_total": "Сумма",
        "q_add": "Добавить в список", "q_clear": "Очистить", "q_create": "💾 СКАЧАТЬ (PDF)",
        "q_inc": "Включено", "q_exc": "Исключено", "q_total": "ОБЩАЯ СУММА", "q_show_total": "Показать общую сумму",
        "q_intro": "Наше предложение относительно продуктов и услуг представлено ниже:",
        "q_del_item": "Удал.", "q_date": "Дата", "q_note_label": "Особые условия / Примечания:", "q_note_ph": "Например, предоплата 50%...",
        "editor": "📝 Редактор контента", "role_active": "Активная роль", "char_count": "Количество символов:",
        "set_logo": "Изменить логотип", "set_logo_btn": "Загрузить логотип", "set_role_mgmt": "Управление ролями",
        "set_add_role": "Добавить новую роль", "set_del_role": "Удалить роль", "set_theme": "Внешний вид и тема",
        "set_api_keys": "🔑 Ключи API", "set_save": "Сохранить (Общие)", "set_admin": "🔐 Управление администрированием",
        "set_modules": "Модули", "set_bg": "Фон", "set_txt": "Цвет текста", "set_btn": "Цвет кнопки"
    },
    "AR": {
        "name": "Arabic",
        "btn_social_main": "📱 إدارة وسائل التواصل", 
        "btn_linkedin": "🔹 لينكد إن",
        "btn_instagram": "📸 إنستغرام",
        "btn_quote": "💼 إنشاء عرض سعر",
        "btn_bimaks_tech": "🧪 تقنيات بيماكس", 
        
        "nav_analysis": "تحليل النظام",
        "nav_roi": "حاسبة العائد على الاستثمار",
        "nav_ocr": "قراءة التقارير بالذكاء الاصطناعي",
        "nav_reg": "اللوائح العالمية",
        
        "solver_title": "تحليل النظام وحساب LSI",
        "solver_ph": "صف المشكلة الحالية بالتفصيل (مثل: ترسبات كلسية مفرطة، تآكل...)",
        "mk_water": "🧪 مياه التعويض (Makeup)",
        "sy_water": "⚗️ مياه النظام (System)",
        "btn_analyze": "🚀 تحليل وإنشاء حل",
        "lsi_result": "📊 نتائج مؤشرات LSI / RSI",
        "lsi_info": "ℹ️ تنبيه: إدخال قيم درجة الحموضة (pH)، الأملاح (TDS)، الحرارة، عسر الكالسيوم، والقلوية إلزامي للحساب التلقائي.",
        
        # Water Analysis Parameters
        "ph_req": "درجة الحموضة (إلزامي)",
        "tds_req": "الأملاح (ppm) (إلزامي)",
        "temp_req": "الحرارة (°C) (إلزامي)",
        "ca_req": "عسر الكالسيوم (إلزامي)",
        "alk_req": "القلوية (إلزامي)",
        "cond_opt": "الموصلية",
        "cl_opt": "الكلوريد",
        "so4_opt": "الكبريتات",
        "fe_opt": "الحديد",
        "sio2_opt": "السيليكا",
        
        "roi_title": "الجرعة الذكية وحاسبة العائد على الاستثمار (ROI)",
        "roi_subtitle_inputs": "⚙️ بيانات التشغيل الحالية",
        "roi_subtitle_costs": "💰 تكاليف الوحدة",
        "roi_subtitle_bimaks": "🧪 أهداف بيماكس",
        
        "roi_vol": "حجم النظام (م³)",
        "roi_blowdown": "معدل التصريف الحالي (م³/ساعة)",
        "roi_hours": "ساعات التشغيل السنوية",
        "roi_coc_curr": "دورات التركيز الحالية (CoC)",
        "roi_scale": "سماكة الترسبات المقدرة (مم)",
        
        "roi_cost_water": "تكلفة وحدة المياه (€/م³)",
        "roi_cost_energy": "إجمالي فاتورة الطاقة السنوية (€)",
        "roi_cost_chem": "التكلفة الكيميائية السنوية (€)",
        
        "roi_coc_target": "دورات التركيز المستهدفة (مع بيماكس)",
        "roi_dose": "الجرعة الموصى بها (جزء في المليون)",
        "roi_price": "سعر وحدة المنتج (€/كجم)",
        
        "roi_calc_btn": "📊 إنشاء تحليل مفصل للعائد على الاستثمار",
        
        "tbl_param": "المعيار",
        "tbl_curr": "الوضع الحالي",
        "tbl_bimaks": "حل بيماكس",
        "tbl_save": "الفرق / التوفير",
        "row_water": "الاستهلاك السنوي للمياه (م³)",
        "row_energy": "تكلفة الطاقة (€)",
        "row_chem": "التكلفة الكيميائية (€)",
        "row_total": "التكلفة الإجمالية (€)",
        
        "ocr_title": "تفسير التقارير (OCR)",
        "ocr_desc": "قم بتحميل صورة تقرير التحليل الذي تلقيته من العميل، ودع الذكاء الاصطناعي يقرأه ويفسره.",
        "ocr_btn": "📷 مسح وتفسير التقرير",
        
        "reg_title": "دليل اللوائح والشهادات العالمية",
        "reg_ph": "مثال: ما هي القيود المفروضة على استخدام الفوسفونات في ألمانيا؟",
        
        "sys_select": "اختر التخصص / الدور:", "sys_manual": "🔹 إدخال دور جديد / يدوي", 
        "sys_placeholder_select": "--- اختر الدور ---", "topic": "موضوع المحتوى / العنوان:", 
        "target_audience": "الجمهور المستهدف:", "target_def": "القارئ العام",
        "target_plat": "منصة النشر:", "plat_def": "LinkedIn",
        "prod_ref": "المنتج / الخدمة للترويج (اختياري):", "prod_link_lbl": "رابط المنتج (اختياري):",
        "detail_info": "معلومات تفصيلية / تقديم:", "btn_create": "إنشاء مقال احترافي",
        "settings": "⚙️ الإعدادات", 
        "visual": "🖼️ تحميل الوسائط (صورة/فيديو)", "visual_desc": "قم بإثراء المحتوى الخاص بك عن طريق تحميل الوسائط.", 
        "publish": "نشر على لينكد إن", "publish_insta": "نشر على إنستغرام",
        "prompt_limit": "الحد الأقصى للأحرف:", "guide_btn": "❓ كيف تحصل على مفاتيح API؟ (دليل)",
        "back_btn": "🔙 العودة للتطبيق", 
        
        "guide_title_main": "🔑 دليل الحصول على مفاتيح API",
        "guide_gemini_title": "1. مفتاح Google Gemini API (مجاني)", 
        "guide_gemini_text": "**الخطوة 1:** اذهب إلى موقع [Google AI Studio](https://aistudio.google.com/) وسجل الدخول بحساب جوجل.\n**الخطوة 2:** انقر على زر **'Get API key'** في القائمة اليسرى.\n**الخطوة 3:** انقر على **'Create API Key'**.\n**الخطوة 4:** انسخ المفتاح الذي يبدأ بـ 'AIza'.\n**الخطوة 5:** الصقه في المربع المخصص في إعدادات هذا التطبيق.",
        "guide_linkedin_title": "2. رمز وصول LinkedIn", 
        "guide_linkedin_text": "**الخطوة 1:** اذهب إلى صفحة [LinkedIn Developers](https://www.linkedin.com/developers/) وأنشئ تطبيقاً.\n**الخطوة 2:** اختر **'Share on LinkedIn'** واطلب الوصول.\n**الخطوة 3:** تحقق من إعدادات OAuth 2.0 في علامة التبويب 'Auth'.\n**الخطوة 4:** افتح **'Token Generator'**.\n**الخطوة 5:** حدد **'openid', 'profile', 'w_member_social'** وقم بإنشاء الرمز.",
        "guide_instagram_title": "3. رمز Instagram ومعرف العمل",
        "guide_instagram_text": "**الخطوة 1:** أنشئ تطبيقاً في [Meta for Developers](https://developers.facebook.com/).\n**الخطوة 2:** أضف 'Instagram Graph API'.\n**الخطوة 3:** افتح **'Graph API Explorer'**.\n**الخطوة 4:** أضف الأذونات **'instagram_basic', 'instagram_content_publish'**.\n**الخطوة 5:** ابحث عن معرف العمل الخاص بك.",

        "step1_linkedin_title": "📋 تفاصيل المحتوى (انقر للتوسيع)",
        "settings_title": "⚙️ إعدادات التطبيق",
        "quote_title": "💼 منشئ عروض الأسعار الاحترافية",
        "q_invoice_info": "اسم الفاتورة / العميل:", "q_shipping_addr": "عنوان الشحن:",
        "q_period": "فترة الصلاحية:", "q_payment": "شروط الدفع:",
        "q_bank_lbl": "المعلومات المصرفية:",
        "q_bank_def": "Vakifbank T.A.O. TR12 0001 5001 5800 7299 3551 65",
        "q_prod_name": "اسم المنتج / الخدمة", "q_packaging": "نوع التغليف", "q_shipping_opt": "الشحن",
        "q_price": "سعر الوحدة", "q_qty": "الكمية", "q_unit": "الوحدة (كجم/قطعة)", "q_line_total": "المبلغ",
        "q_add": "إضافة للقائمة", "q_clear": "مسح", "q_create": "💾 تحميل العرض (PDF)",
        "q_inc": "مشمول", "q_exc": "غير مشمول", "q_total": "المجموع الإجمالي", "q_show_total": "إظهار المجموع الإجمالي",
        "q_intro": "عرضنا بخصوص منتجاتنا وخدماتنا مقدم لكم كالتالي:",
        "q_del_item": "حذف", "q_date": "التاريخ", "q_note_label": "ملاحظات سفلية / شروط خاصة:", "q_note_ph": "مثال: دفعة مقدمة 50%...",
        "editor": "📝 محرر المحتوى", "role_active": "الدور النشط", "char_count": "عدد الأحرف:",
        "set_logo": "تغيير شعار التطبيق", "set_logo_btn": "تحميل الشعار", "set_role_mgmt": "إدارة الأدوار",
        "set_add_role": "إضافة دور جديد", "set_del_role": "حذف الدور", "set_theme": "المظهر والسمة",
        "set_api_keys": "🔑 مفاتيح API", "set_save": "حفظ (عام)", "set_admin": "🔐 إدارة النظام والوحدات",
        "set_modules": "الوحدات", "set_bg": "الخلفية", "set_txt": "لون النص", "set_btn": "لون الزر"
    }
}
