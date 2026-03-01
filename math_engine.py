import math

def calculate_advanced_roi(blowdown_curr, hours, coc_curr, coc_target, water_cost, energy_bill_total, scale_mm, chem_cost):
    try:
        coc_curr = float(coc_curr)
        coc_target = float(coc_target)
        if coc_curr <= 1 or coc_target <= 1: return None 
        evaporation = float(blowdown_curr) * (coc_curr - 1)
        blowdown_new = evaporation / (coc_target - 1)
        water_saved_total = (float(blowdown_curr) - blowdown_new) * float(hours)
        scale_loss_ratio = min(float(scale_mm) * 0.10, 0.50) 
        energy_saved = float(energy_bill_total) * scale_loss_ratio
        return {
            "w_curr": float(blowdown_curr) * float(hours), "w_new": blowdown_new * float(hours),
            "w_save": water_saved_total, "w_money": water_saved_total * float(water_cost),
            "e_save": energy_saved, "total_gain": (water_saved_total * float(water_cost)) + energy_saved - float(chem_cost)
        }
    except: return None

def calculate_lsi(ph, tds, temp_c, ca_hard, alk):
    try:
        ph, tds, temp_c, ca_hard, alk = float(ph), float(tds), float(temp_c), float(ca_hard), float(alk)
        A = (math.log10(tds) - 1) / 10
        B = -13.12 * math.log10(temp_c + 273) + 34.55
        C = math.log10(ca_hard) - 0.4
        D = math.log10(alk)
        pHs = (9.3 + A + B) - (C + D)
        return ph - pHs, 2 * pHs - ph
    except: return None, None