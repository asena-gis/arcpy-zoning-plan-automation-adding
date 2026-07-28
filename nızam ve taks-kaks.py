import arcpy

# 1. AYARLAR
gdb = r"C:\Users\asena.bozdag\Desktop\akillandirma\deneme.gdb"
arcpy.env.workspace = gdb
arcpy.env.overwriteOutput = True

polygon_fc = "polygon"
circle_fc = "daire"
annotation_fc = "yazi"

def parse_val(val):
    if val is None: return None
    try:
        clean = "".join(c for c in str(val) if c.isdigit() or c in ".,")
        return float(clean.replace(",", ".").strip())
    except: return None

# 2. KATMAN VE SEÇİM KONTROLÜ
poly_lyr = "polygon" 

if not arcpy.Exists(poly_lyr):
    arcpy.management.MakeFeatureLayer(polygon_fc, poly_lyr)

desc = arcpy.Describe(poly_lyr)
selection_count = 0
if hasattr(desc, "fidSet"): 
    selection_count = len(desc.fidSet.split(";")) if desc.fidSet else 0

all_fields = {f.name.lower(): f.name for f in arcpy.ListFields(polygon_fc)}
f_kat = all_fields.get("katadedi") or "katadedi"
f_taks = all_fields.get("taks") or "taks"
f_kaks = all_fields.get("kaks") or "kaks"
f_etkin = all_fields.get("etkinmi") or "etkinmi"

f_onbahce = all_fields.get("onbahcemesafesi") or "onbahcemesafesi"
f_yanbahce = all_fields.get("yanbahcemesafesi") or "yanbahcemesafesi"

where_clause = f"{f_etkin} = 0"

# 3. YAZI KATMANI HAFIZAYA ALMA
all_annos = []
yazi_fields = {f.name.lower(): f.name for f in arcpy.ListFields(annotation_fc)}
f_yazi_etkin = yazi_fields.get("etkin_durumu") or yazi_fields.get("etkindurumu")

if f_yazi_etkin:
    yazi_where = f"{f_yazi_etkin} = 0"
    with arcpy.da.SearchCursor(annotation_fc, ["textstring", "SHAPE@"], where_clause=yazi_where) as sc:
        for row in sc:
            if row and row[1]: all_annos.append({"txt": str(row[0]).strip(), "geom": row[1]})
else:
    with arcpy.da.SearchCursor(annotation_fc, ["textstring", "SHAPE@"]) as sc:
        for row in sc:
            if row and row[1]: all_annos.append({"txt": str(row[0]).strip(), "geom": row[1]})

# 4. DAİRE KATMANI HAFIZAYA ALMA
daire_fields = {f.name.lower(): f.name for f in arcpy.ListFields(circle_fc)}
f_daire_etkin = daire_fields.get("etkinmi") or "etkinmi"
all_daire = []

if f_daire_etkin in daire_fields.values():
    daire_where = f"{f_daire_etkin} = 0"
    all_daire = [row[0] for row in arcpy.da.SearchCursor(circle_fc, ["SHAPE@"], where_clause=daire_where) if row and row[0]]
else:
    all_daire = [row[0] for row in arcpy.da.SearchCursor(circle_fc, ["SHAPE@"]) if row and row[0]]

# 5. CURSOR YAPILANDIRMASI
cursor_fields = ["SHAPE@", f_kat, f_taks, f_kaks, "OID@", f_onbahce, f_yanbahce]

# 6. ANA GÜNCELLEME DÖNGÜSÜ
with arcpy.da.UpdateCursor(poly_lyr, cursor_fields, where_clause=where_clause) as ucursor:
    updated_count = 0
    for row in ucursor:
        poly_geom, kat_val, taks_val, kaks_val, poly_oid, on_val, yan_val = row
        if not poly_geom: continue

        t_res, k_res, kat_res = None, None, None
        on_bahce_res, yan_bahce_res = None, None
        daire_bulundu = False

        polygon_icindeki_yazilar = [a for a in all_annos if poly_geom.contains(a["geom"].centroid)]

        # --- KRİTİK İSTİSNA: Parselde emsal değeri (E=...) yazılı ise doldurmadan geç ---
        emsal_yazisi_var_mi = any(o["txt"].upper().startswith("E=") or o["txt"].upper().startswith("E:") for o in polygon_icindeki_yazilar)
        if emsal_yazisi_var_mi:
            print(f"⏭️ OID {poly_oid} emsal değerli alan olduğu için kolonlar boş bırakıldı (Atlandı).")
            continue

        # --- ADIM A: DAİRE TABANLI VERİ TOPLAMA ---
        for c_geom in all_daire:
            ext = c_geom.extent
            c_center = arcpy.Point((ext.XMin + ext.XMax)/2.0, (ext.YMin + ext.YMax)/2.0)
            
            if poly_geom.contains(c_center) or poly_geom.distanceTo(c_center) < 3.0:
                daire_bulundu = True
                daire_ici_yazilar = [a for a in polygon_icindeki_yazilar if c_geom.contains(a["geom"].centroid) or a["geom"].distanceTo(c_center) < 1.5]

                # 1. TAKS / KAKS Ayıkla
                ondalikli_yazilar = []
                for o in daire_ici_yazilar:
                    if "." in o["txt"] or "," in o["txt"]:
                        val = parse_val(o["txt"])
                        if val is not None and val < 10.0:
                            ondalikli_yazilar.append({"val": val, "y": o["geom"].centroid.Y})

                if len(ondalikli_yazilar) >= 2:
                    ondalikli_yazilar.sort(key=lambda item: item["y"], reverse=True)
                    t_res = ondalikli_yazilar[0]["val"]   
                    k_res = ondalikli_yazilar[-1]["val"]  
                elif len(ondalikli_yazilar) == 1:
                    tek_deger = ondalikli_yazilar[0]["val"]
                    if tek_deger < 1.0: t_res = tek_deger
                    else: k_res = tek_deger

                # 2. DAİRE İÇİNDEKİ BAHÇE MESAFELERİNİ AYIKLAMA
                nizam_obj = next((o for o in daire_ici_yazilar if any(c.isalpha() for c in o["txt"])), None)
                if nizam_obj:
                    daire_ici_tam_sayilar = []
                    for o in daire_ici_yazilar:
                        if o != nizam_obj and o["txt"].replace(".","").replace(",","").isdigit():
                            val = parse_val(o["txt"])
                            # 🎯 HERHANGİ BİR DEĞER OLABİLİR: Sayı sınırlaması kaldırıldı, daire içindeki tüm tam sayılar taranır
                            if val is not None and 0 < val < 30: 
                                daire_ici_tam_sayilar.append({"val": float(val), "x": o["geom"].centroid.X, "y": o["geom"].centroid.Y})
                    
                    if len(daire_ici_tam_sayilar) >= 2:
                        # Konum sıralaması (Üstteki/Sağdaki Ön Bahçe, Alttaki Yan Bahçe)
                        daire_ici_tam_sayilar.sort(key=lambda item: item["y"], reverse=True)
                        on_bahce_res = daire_ici_tam_sayilar[0]["val"]  
                        yan_bahce_res = daire_ici_tam_sayilar[-1]["val"] 

        # --- ADIM B: BAĞIMSIZ DIŞ METİN KONTROLLERİ (Daire içi boşsa veya dışarıda yazıyorsa) ---
        if on_bahce_res is None or yan_bahce_res is None:
            poly_boundary = poly_geom.boundary()
            bahce_adaylari = []

            for o in polygon_icindeki_yazilar:
                txt = o["txt"].strip()
                val = parse_val(txt)
                # 🎯 HERHANGİ BİR DEĞER OLABİLİR: 1.0 ile 20.0 metre arasındaki tüm mantıklı çekme mesafelerini listeler
                if val is not None and 1.0 <= val <= 20.0:
                    dist_to_boundary = o["geom"].distanceTo(poly_boundary)
                    bahce_adaylari.append({"val": val, "dist_edge": dist_to_boundary})

            if bahce_adaylari:
                # Sınıra (yola) en yakın olanları sırala
                bahce_adaylari.sort(key=lambda item: item["dist_edge"])
                if on_bahce_res is None: 
                    on_bahce_res = bahce_adaylari[0]["val"]
                
                farkli_adaylar = [b["val"] for b in bahce_adaylari if b["val"] != on_bahce_res]
                if farkli_adaylar and yan_bahce_res is None:
                    yan_bahce_res = farkli_adaylar[0]

        # --- ADIM C: İMAR MATEMATİĞİ GÜVENCESİ (Kat Adedi) ---
        if kat_res is None and t_res is not None and k_res is not None and t_res > 0:
            kat_res = int(round(k_res / t_res))

        if not daire_bulundu and on_bahce_res is None and yan_bahce_res is None:
            continue

        # Tabloya değerleri doğrudan yazdırıyoruz
        if kat_res is not None: row[1] = int(kat_res)
        if t_res is not None: row[2] = float(t_res)
        if k_res is not None: row[3] = float(k_res)
        if on_bahce_res is not None: row[5] = float(on_bahce_res)
        if yan_bahce_res is not None: row[6] = float(yan_bahce_res)
        
        ucursor.updateRow(row)
        print(f"✅ OID {poly_oid} güncellendi -> TAKS: {t_res}, KAKS: {k_res}, KAT: {kat_res}, ÖNBAHÇE: {on_bahce_res}, YANBAHÇE: {yan_bahce_res}")
        updated_count += 1

print(f"🏁 İşlem bitti. Güncellenen: {updated_count}")
