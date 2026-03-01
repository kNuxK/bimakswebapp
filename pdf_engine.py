import io
import os
import requests
import textwrap
import re
from PIL import Image, ImageDraw, ImageFont
import config

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    from pypdf import PdfWriter, PdfReader
    HAS_PYPDF = True
except ImportError:
    try:
        from PyPDF2 import PdfWriter, PdfReader
        HAS_PYPDF = True
    except ImportError:
        HAS_PYPDF = False

try:
    import fitz 
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

def register_embedded_font():
    font_path = "DejaVuSans.ttf"
    if not os.path.exists(font_path):
        try:
            url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
            r = requests.get(url, timeout=10)
            if r.status_code == 200:
                with open(font_path, "wb") as f: f.write(r.content)
        except: return None
    if os.path.exists(font_path):
        try: pdfmetrics.registerFont(TTFont('TrFont', font_path)); return "TrFont"
        except: return None
    return None

def create_pdf(invoice_info, shipping_addr, period, payment, bank_info, items, currency, show_total, custom_note, lang_code):
    if not HAS_REPORTLAB: return None
    import streamlit as st
    t = lambda k: config.LANGUAGES.get(lang_code, config.LANGUAGES['TR']).get(k, k)
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4); width, height = A4
    f_reg = register_embedded_font() or "Helvetica"
    
    is_pdf_template = False
    template_bytes = st.session_state.get('template_data')
    if template_bytes:
        if isinstance(template_bytes, bytes) and b'%PDF' in template_bytes[:50]: is_pdf_template = True
        else:
            try: c.drawImage(ImageReader(io.BytesIO(template_bytes)), 0, 0, width=width, height=height)
            except: pass

    start_y = height - 190
    c.setFont(f_reg, 10); c.drawString(50, start_y, t('q_invoice_info'))
    txt = c.beginText(50, start_y - 15); txt.setFont(f_reg, 10)
    for l in invoice_info.split('\n'): txt.textLine(l[:50])
    c.drawText(txt)
    
    c.setFont(f_reg, 10); c.drawString(350, start_y, f"{t('q_date')}: {datetime.now().strftime('%d.%m.%Y')}")
    c.drawString(350, start_y - 20, f"{t('q_period')} {period}")
    c.drawString(350, start_y - 35, f"{t('q_payment')} {payment}")
    
    y = start_y - 120; c.line(40, y+15, 560, y+15); c.setFont(f_reg, 9)
    amb_text = {"TR":"Ambalaj", "EN":"Package", "RU":"Упаковка", "AR":"التعبئة", "FR":"Emballage", "ES":"Paquete"}.get(lang_code, "Ambalaj")
    c.drawString(40, y, t('q_prod_name')); c.drawString(220, y, amb_text); c.drawString(450, y, f"{t('q_price')} ({currency})")
    
    y -= 20; grand_total = 0
    for it in items:
        try:
            p = float(it.get('price', 0)); q = float(it.get('qty', 1)); line_total = p * q; grand_total += line_total
            name_text = str(it.get('name', '')); wrapped_name = textwrap.wrap(name_text, width=35) 
            if not wrapped_name: wrapped_name = [""]
            c.drawString(40, y, wrapped_name[0]); c.drawString(220, y, str(it.get('pkg', ''))[:15]); c.drawString(450, y, f"{p:,.2f}"); y -= 15
            if len(wrapped_name) > 1:
                for extra_line in wrapped_name[1:]: c.drawString(40, y, extra_line); y -= 15
            y -= 5 
        except: continue
    
    if show_total: 
        c.setFont(f_reg, 11); c.line(40, y, 560, y); c.drawString(350, y-20, f"{t('q_total')}: {grand_total:,.2f} {currency}")
    
    bank_y = 100; c.setFont(f_reg, 9); c.drawString(50, bank_y, t('q_bank_lbl')); c.drawString(140, bank_y, bank_info.replace('\n', ' | '))
    c.save(); buffer.seek(0)
    
    if is_pdf_template and HAS_PYPDF:
        try:
            text_pdf = PdfReader(buffer); template_pdf = PdfReader(io.BytesIO(template_bytes)); writer = PdfWriter()
            template_page = template_pdf.pages[0]; text_page = text_pdf.pages[0]
            if hasattr(template_page, "merge_page"): template_page.merge_page(text_page)
            elif hasattr(template_page, "mergePage"): template_page.mergePage(text_page)
            writer.add_page(template_page); merged_buffer = io.BytesIO(); writer.write(merged_buffer); merged_buffer.seek(0); return merged_buffer
        except Exception as e: return buffer
    return buffer

def create_generated_document_pdf(text_content, logo_bytes=None, footer_text=None, lang_code="TR", header_params=None):
    if not HAS_REPORTLAB: return None
    buffer = io.BytesIO()
    width, height = A4
    c = canvas.Canvas(buffer, pagesize=A4)
    font_name = register_embedded_font() or "Helvetica"
    
    def draw_bg(canvas_obj, page_num):
        if logo_bytes:
            try:
                logo_img = ImageReader(io.BytesIO(logo_bytes))
                pil_img = Image.open(io.BytesIO(logo_bytes))
                aspect = pil_img.height / float(pil_img.width)
                w = 120
                h = w * aspect
                if h > 50:
                    h = 50
                    w = h / aspect
                canvas_obj.drawImage(logo_img, width - w - 40, height - h - 20, width=w, height=h, preserveAspectRatio=True, mask='auto')
            except: pass
            
        # V 133.0: TARİHLER SOL TARAFA (X=40) HİZALANDI - LOGOYLA ÇAKIŞMAZ
        if header_params and page_num == 1:
            canvas_obj.setFont(font_name, 9)
            canvas_obj.setFillColorRGB(0, 0, 0)
            hy = height - 25
            if header_params.get('c_date') and header_params.get('c_date') != '-':
                canvas_obj.drawString(40, hy, f"Oluşturma Tarihi: {header_params['c_date']}")
                hy -= 12
            if header_params.get('r_date') and header_params.get('r_date') != '-':
                canvas_obj.drawString(40, hy, f"Revizyon Tarihi: {header_params['r_date']}")
                hy -= 12
            if header_params.get('vers') and header_params.get('vers') != '-':
                canvas_obj.drawString(40, hy, f"Versiyon: {header_params['vers']}")
        
        canvas_obj.setStrokeColorRGB(0.7, 0.7, 0.7)
        canvas_obj.setLineWidth(1)
        canvas_obj.line(40, height - 80, width - 40, height - 80) 
        canvas_obj.line(40, 60, width - 40, 60) 
        
        if footer_text:
            canvas_obj.setFont(font_name, 8)
            canvas_obj.setFillColorRGB(0.3, 0.3, 0.3)
            lines = footer_text.split('\n')
            y_start = 48
            for l in lines:
                canvas_obj.drawString(40, y_start, l.strip()[:150])
                y_start -= 10
        
        canvas_obj.setFont(font_name, 8)
        canvas_obj.setFillColorRGB(0.3, 0.3, 0.3)
        canvas_obj.drawRightString(width - 40, 48, f"Sayfa {page_num}")
        canvas_obj.setFillColorRGB(0, 0, 0)
    
    page_num = 1
    draw_bg(c, page_num)
    text_y = height - 110
    
    if text_content:
        # Temizlik ve ayrıştırma
        text_content = text_content.replace('(AI_LUTFEN_HESAPLA)', '').replace('[AI_ESTIMATE]', '')
        
        for p in text_content.split('\n'):
            p = p.strip()
            if not p:
                text_y -= 8
                continue
            
            # V 133.0: PİKTOGRAM GÖRSEL MOTORU EKLENDİ
            img_matches = re.findall(r'!\[.*?\]\((.*?)\)', p)
            clean_p = re.sub(r'!\[.*?\]\(.*?\)', '', p).strip() # Yazıdan linki sil
            clean_p = clean_p.replace('#', '').replace('**', '').replace('*', '').strip()
            
            # V 133.0: AÇIK GRİ BAŞLIK FONU (HEADER BANNER)
            is_main_header = clean_p.upper().startswith('BÖLÜM') or clean_p.upper().startswith('SECTION')
            is_sub_header = p.startswith('##') or p.startswith('###')
            
            if is_main_header or is_sub_header:
                c.setFillColorRGB(0.92, 0.92, 0.95) # Açık gri-mavi
                c.rect(35, text_y - 4, 520, 18, fill=1, stroke=0)
                c.setFillColorRGB(0, 0, 0)
                c.setFont(font_name, 11)
            else:
                c.setFont(font_name, 9)
            
            # V 133.0: GÜÇLENDİRİLMİŞ TABLO MOTORU
            if clean_p.startswith('|') and clean_p.endswith('|'):
                if clean_p.replace('|', '').replace('-', '').replace(':', '').replace(' ', '') == '':
                    continue # Tablo ayraçlarını atla
                
                cols = [col.strip() for col in clean_p.strip('|').split('|')]
                col_count = len(cols)
                
                if col_count == 5: col_bounds = [40, 150, 220, 290, 400, 555]
                elif col_count == 4: col_bounds = [40, 180, 280, 400, 555]
                else:
                    step = 515 / max(1, col_count)
                    col_bounds = [40 + int(i*step) for i in range(col_count+1)]
                    
                c.setLineWidth(0.5)
                c.setStrokeColorRGB(0.7, 0.7, 0.7)
                c.line(40, text_y + 10, 555, text_y + 10) 
                
                col_wrapped = []
                for i, col_txt in enumerate(cols):
                    if i < len(col_bounds) - 1:
                        col_w = col_bounds[i+1] - col_bounds[i]
                        char_w = max(5, int(col_w / 5.5))
                        wrapped = textwrap.wrap(col_txt, width=char_w) if col_txt else [""]
                    else:
                        wrapped = [col_txt[:20]]
                    col_wrapped.append(wrapped)
                    
                max_lines = max([len(w) for w in col_wrapped]) if col_wrapped else 1
                row_start_y = text_y + 10
                
                for line_idx in range(max_lines):
                    if text_y < 85: 
                        c.line(40, text_y + 10, 555, text_y + 10)
                        for b in col_bounds: c.line(b, row_start_y, b, text_y + 10)
                        c.showPage()
                        page_num += 1
                        draw_bg(c, page_num)
                        text_y = height - 110
                        c.setFont(font_name, 9)
                        row_start_y = text_y + 10
                        c.line(40, text_y + 10, 555, text_y + 10)
                    
                    for i, cw_list in enumerate(col_wrapped):
                        if i < len(col_bounds) - 1 and line_idx < len(cw_list):
                            c.drawString(col_bounds[i] + 5, text_y, cw_list[line_idx])
                    text_y -= 12
                    
                c.line(40, text_y + 10, 555, text_y + 10) 
                for b in col_bounds:
                    c.line(b, row_start_y, b, text_y + 10) 
                
                text_y -= 4
                continue
            
            clean_p = clean_p.replace('|', '')
            wrapped = textwrap.wrap(clean_p, width=105) if clean_p else [""]
            
            for wl in wrapped:
                if text_y < 85: 
                    c.showPage()
                    page_num += 1
                    draw_bg(c, page_num)
                    text_y = height - 110
                    if is_main_header or is_sub_header: c.setFont(font_name, 11)
                    else: c.setFont(font_name, 9)
                    
                c.drawString(40, text_y, wl)
                text_y -= 12
            text_y -= 4 
            
            # Eğer satırda Piktogram linki varsa o resmi PDF'e bas!
            if img_matches:
                img_x = 40
                text_y -= 5 
                for img_url in img_matches:
                    try:
                        r = requests.get(img_url, stream=True, timeout=5)
                        if r.status_code == 200:
                            pil_img = Image.open(io.BytesIO(r.content)).convert("RGBA")
                            c.drawImage(ImageReader(pil_img), img_x, text_y - 40, width=40, height=40, preserveAspectRatio=True, mask='auto')
                            img_x += 50
                    except: pass
                if img_matches:
                    text_y -= 45 # Resimler için boşluk bırak
            
    c.save()
    buffer.seek(0)
    return buffer.getvalue()

def replace_text_in_pdf_bytes(pdf_bytes, auto_data, exact_replacements=None):
    if not HAS_PYMUPDF or not pdf_bytes: return pdf_bytes
    if not auto_data and not exact_replacements: return pdf_bytes
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        old_prod = ""
        table_prod_x0 = 150 
        if auto_data:
            try:
                for page in doc:
                    insts = page.search_for("ÜRÜN ADI")
                    if insts:
                        words = page.get_text("words")
                        tw = [w for w in words if w[1] < insts[0].y1+2 and w[3] > insts[0].y0-2 and w[0] >= insts[0].x1-2]
                        if tw:
                            tw.sort(key=lambda x: x[0])
                            old_prod = " ".join([w[4] for w in tw])
                            table_prod_x0 = tw[0][0] 
                            break
            except: pass

        for page in doc:
            try:
                for link in page.get_links(): 
                    page.delete_link(link)
            except: pass
            
            if auto_data and old_prod and auto_data.get("ÜRÜN ADI") and auto_data["ÜRÜN ADI"][1]:
                new_prod = str(auto_data["ÜRÜN ADI"][1])
                o_insts = page.search_for(old_prod)
                for inst in o_insts:
                    rect = fitz.Rect(inst.x0 - 1, inst.y0 - 2, inst.x1 + 1, inst.y1 + 2)
                    page.add_redact_annot(rect, fill=(1,1,1))
                    page.apply_redactions()
                    if page.number == 0: fsz = (inst.y1 - inst.y0) * 0.75
                    else: fsz = (inst.y1 - inst.y0) * 0.60 
                    if fsz < 5: fsz = 8
                    page.insert_text((inst.x0, inst.y1 - 1.5), new_prod, fontsize=fsz, color=(0,0,0), fontname="helv")

            if page.number == 0 and auto_data:
                if auto_data.get("ADDRESS") and auto_data["ADDRESS"][1]:
                    new_add = auto_data["ADDRESS"][1]
                    inst_ted = page.search_for("TEDARİKÇİ")
                    inst_tel = page.search_for("Tel:")
                    if not inst_tel: inst_tel = page.search_for("Tel :")
                    if not inst_tel: inst_tel = page.search_for("Tel")
                    if inst_ted and inst_tel:
                        ted = inst_ted[0]
                        valid_tels = [t for t in inst_tel if t.y0 > ted.y1]
                        if valid_tels:
                            valid_tels.sort(key=lambda t: t.y0)
                            tel = valid_tels[0]
                            if (tel.y0 - ted.y1) < 150: 
                                words_pg0 = page.get_text("words")
                                t_words = [w for w in words_pg0 if w[1] < ted.y1+3 and w[3] > ted.y0-3 and w[0] >= ted.x1-2]
                                addr_x = min(w[0] for w in t_words) if t_words else ted.x1 + 10
                                addr_y0 = ted.y1 + 2
                                addr_y1 = min(tel.y0 - 2, addr_y0 + 60)
                                if addr_y1 > addr_y0:
                                    rect = fitz.Rect(addr_x - 2, addr_y0, page.rect.width - 20, addr_y1)
                                    page.add_redact_annot(rect, fill=(1,1,1))
                                    page.apply_redactions()
                                    y_cursor = addr_y0 + 10
                                    for line in new_add.split('\n'):
                                        page.insert_text((addr_x, y_cursor), line.strip(), fontsize=9, color=(0,0,0), fontname="helv")
                                        y_cursor += 12

            if auto_data:
                words = page.get_text("words")
                processed_keys = set()
                for key, (separator, new_val) in auto_data.items():
                    if not new_val or key == "ADDRESS" or key == "ÜRÜN ADI": continue 
                    base_key = key.replace(":", "").strip()
                    if base_key in processed_keys: continue
                    insts = page.search_for(key)
                    if insts:
                        processed_keys.add(base_key)
                        for inst in insts:
                            tw = [w for w in words if w[1] < inst.y1+3 and w[3] > inst.y0-3 and w[0] >= inst.x1-2]
                            if tw:
                                min_x = min(w[0] for w in tw)
                                max_x = max(w[2] for w in tw)
                                if base_key in ["KİMYASAL ADI", "TEDARİKÇİ", "BAŞVURULACAK KİŞİ", "ACİL DURUM TELEFONU", "ACİL DURUM TEL"]:
                                    start_x = table_prod_x0 
                                elif base_key in ["Tel", "Fax", "E-mail", "Web"]:
                                    start_x = inst.x0 + 40  
                                elif base_key in ["Oluşturma Tarihi", "Revizyon Tarihi", "Versiyon"]:
                                    start_x = inst.x0 + 90  
                                else:
                                    start_x = inst.x1 + 4
                                safe_left_bound = inst.x1 + 2
                                start_x = max(start_x, safe_left_bound)
                                wipe_x = min(min_x, start_x) - 2
                                wipe_x = max(wipe_x, safe_left_bound)
                                rect = fitz.Rect(wipe_x, inst.y0, max_x + 5, inst.y1)
                                page.add_redact_annot(rect, fill=(1,1,1))
                                page.apply_redactions()
                                fsz = (inst.y1 - inst.y0) * 0.75
                                if fsz < 6: fsz = 9
                                final_text = f"{separator}{new_val}"
                                page.insert_text((start_x, inst.y1 - 1.5), final_text, fontsize=fsz, color=(0,0,0), fontname="helv")

            if exact_replacements:
                for item in exact_replacements:
                    if len(item) == 4: old_text, new_text, is_bold, is_center = item
                    else: old_text, new_text, is_bold, is_center = item[0], item[1], False, False
                    if old_text and new_text and str(old_text).strip() != "" and str(new_text).strip() != "":
                        text_instances = page.search_for(str(old_text))
                        for inst in text_instances:
                            will_center = False
                            if is_center and inst.y1 < 150: will_center = True
                            rect = fitz.Rect(inst.x0 - 1, inst.y0 - 2, inst.x1 + 1, inst.y1 + 2)
                            page.add_redact_annot(rect, fill=(1, 1, 1))
                            page.apply_redactions()
                            fsz = (inst.y1 - inst.y0) * 0.75
                            if fsz < 6: fsz = 9
                            font_to_use = "hebo" if is_bold else "helv"
                            if will_center:
                                try:
                                    font = fitz.Font(font_to_use)
                                    text_width = font.text_length(str(new_text), fontsize=fsz)
                                    target_x = (page.rect.width - text_width) / 2
                                except: target_x = inst.x0
                            else: target_x = inst.x0 
                            page.insert_text((target_x, inst.y1 - 1.5), str(new_text), fontsize=fsz, color=(0,0,0), fontname=font_to_use)
        output = io.BytesIO()
        doc.save(output)
        output.seek(0)
        return output.read()
    except Exception as e:
        return pdf_bytes

def create_dealer_pdf(original_pdf_bytes, dealer_logo_bytes, dealer_address, 
                      top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                      bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                      logo_x, logo_y, logo_w, addr_x, addr_y, lang_code, 
                      auto_data=None, exact_replacements=None):
    if not HAS_PYPDF or not HAS_REPORTLAB: return None
    if auto_data or exact_replacements:
        original_pdf_bytes = replace_text_in_pdf_bytes(original_pdf_bytes, auto_data, exact_replacements)
    try:
        original_pdf = PdfReader(io.BytesIO(original_pdf_bytes))
        writer = PdfWriter()
        packet = io.BytesIO()
        width, height = 595.27, 841.89
        try:
            first_page = original_pdf.pages[0] if hasattr(original_pdf, "pages") else original_pdf.getPage(0)
            mbox = first_page.mediabox if hasattr(first_page, "mediabox") else first_page.mediaBox
            width = float(mbox.width) if hasattr(mbox, "width") else (float(mbox.getWidth()) if hasattr(mbox, "getWidth") else float(mbox[2]))
            height = float(mbox.height) if hasattr(mbox, "height") else (float(mbox.getHeight()) if hasattr(mbox, "getHeight") else float(mbox[3]))
        except: pass
        c = canvas.Canvas(packet, pagesize=(width, height))
        if top_mask_h > 0 and top_mask_w > 0:
            c.setFillColorRGB(1, 1, 1)
            c.rect(top_mask_x, height - top_mask_y - top_mask_h, top_mask_w, top_mask_h, fill=1, stroke=0)
        if bot_mask_h > 0 and bot_mask_w > 0:
            c.setFillColorRGB(1, 1, 1)
            c.rect(bot_mask_x, height - bot_mask_y - bot_mask_h, bot_mask_w, bot_mask_h, fill=1, stroke=0)
        if dealer_logo_bytes:
            try:
                logo_img = ImageReader(io.BytesIO(dealer_logo_bytes))
                pil_img = Image.open(io.BytesIO(dealer_logo_bytes))
                aspect = pil_img.height / pil_img.width
                logo_h = logo_w * aspect
                c.drawImage(logo_img, logo_x, height - logo_y - logo_h, width=logo_w, height=logo_h, preserveAspectRatio=True, mask='auto')
            except: pass
        if dealer_address:
            try:
                f_reg = register_embedded_font() or "Helvetica"
                c.setFont(f_reg, 9)
                c.setFillColorRGB(0, 0, 0) 
                txt = c.beginText(addr_x, height - addr_y) 
                for line in dealer_address.split('\n'):
                    txt.textLine(line[:150])
                c.drawText(txt)
            except: pass
        c.save()
        packet.seek(0)
        overlay_pdf = PdfReader(packet)
        overlay_page = overlay_pdf.pages[0] if hasattr(overlay_pdf, "pages") else overlay_pdf.getPage(0)
        pages_list = original_pdf.pages if hasattr(original_pdf, "pages") else [original_pdf.getPage(i) for i in range(original_pdf.getNumPages())]
        for page in pages_list:
            if hasattr(page, "merge_page"): page.merge_page(overlay_page)
            elif hasattr(page, "mergePage"): page.mergePage(overlay_page)
            writer.add_page(page)
        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
        return output
    except Exception as e:
        return None

def generate_sds_preview(original_pdf_bytes, dealer_logo_bytes, dealer_address, 
                         top_mask_x, top_mask_y, top_mask_w, top_mask_h, 
                         bot_mask_x, bot_mask_y, bot_mask_w, bot_mask_h, 
                         logo_x, logo_y, logo_w, addr_x, addr_y, 
                         auto_data=None, exact_replacements=None):
    width, height = 595, 842 
    img = None
    if original_pdf_bytes and HAS_PYMUPDF:
        if auto_data or exact_replacements:
            original_pdf_bytes = replace_text_in_pdf_bytes(original_pdf_bytes, auto_data, exact_replacements)
        try:
            doc = fitz.open(stream=original_pdf_bytes, filetype="pdf")
            page = doc.load_page(0)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5)) 
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.resize((width, height), Image.Resampling.LANCZOS) 
        except: pass
    if img is None:
        img = Image.new('RGB', (width, height), color=(240, 240, 240)) 
        draw = ImageDraw.Draw(img)
        draw.text((40, 400), "ORIJINAL PDF GORUNTUSU ICIN LUTFEN 'PyMuPDF' KUTUPHANESINI YUKLEYIN", fill=(150, 150, 150))
    draw = ImageDraw.Draw(img)
    if top_mask_h > 0 and top_mask_w > 0:
        draw.rectangle([top_mask_x, top_mask_y, top_mask_x + top_mask_w, top_mask_y + top_mask_h], fill=(255, 255, 255), outline=(200, 0, 0)) 
    if bot_mask_h > 0 and bot_mask_w > 0:
        draw.rectangle([bot_mask_x, bot_mask_y, bot_mask_x + bot_mask_w, bot_mask_y + bot_mask_h], fill=(255, 255, 255), outline=(200, 0, 0)) 
    if dealer_logo_bytes:
        try:
            logo = Image.open(io.BytesIO(dealer_logo_bytes)).convert("RGBA")
            aspect = logo.height / logo.width
            logo_h = int(logo_w * aspect)
            logo = logo.resize((int(logo_w), logo_h), Image.Resampling.LANCZOS)
            img.paste(logo, (int(logo_x), int(logo_y)), logo)
        except: pass
    if dealer_address:
        try:
            font = ImageFont.load_default()
            y_text = addr_y 
            for line in dealer_address.split('\n'):
                draw.text((addr_x, y_text), line[:150], fill=(0, 0, 0), font=font)
                y_text += 12 
        except: pass
    return img
