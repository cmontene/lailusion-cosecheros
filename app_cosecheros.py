"""
Aplicativo de rendimiento de cosecheros — Hacienda La Ilusión SAS
Fuente: CicloDeFruta_2025-2026.xlsx
Uso:  streamlit run app_cosecheros.py
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from pathlib import Path

st.set_page_config(
    page_title="Cosecheros · La Ilusión",
    page_icon="🌴",
    layout="wide",
    initial_sidebar_state="expanded",
)

EXCEL = Path(__file__).parent / "CicloDeFruta_2025-2026.xlsx"

# colores por tipo de labor y por zona
T_COL = {"Cortador": "#5B9BD5", "Alzador": "#70AD47", "Pepeador": "#ED7D31"}
T_BG  = {"Cortador": "#DEEAF1", "Alzador": "#E2EFDA",  "Pepeador": "#FCE4D6"}
Z_COL = {"Zona 1": "#5B9BD5", "Zona 2": "#ED7D31", "Zona 3": "#70AD47", "Zona 4": "#9E7FBF"}
DARK  = "#1F3864"; ORG = "#C55A11"; LGRAY = "#D9D9D9"

st.markdown("""
<style>
[data-testid="stSidebar"] { background:#eef2f9; }
.block-container { padding-top:3rem; }
h1 { color:#1F3864; font-size:1.5rem; margin-bottom:0.2rem; }
h2,h3 { color:#1F3864; }
.kpi { background:white; border:1px solid #D9E1F2; border-left:5px solid #1F3864;
       border-radius:6px; padding:10px 14px; text-align:center; }
.kpi-val { font-size:1.4rem; font-weight:700; color:#1F3864; line-height:1.2; }
.kpi-lbl { font-size:0.67rem; color:#666; text-transform:uppercase; letter-spacing:.05em; }
.kpi-cort{ border-left-color:#5B9BD5; }
.kpi-alz { border-left-color:#70AD47; }
.kpi-pep { border-left-color:#ED7D31; }
.band { background:#D9E1F2; border-radius:8px; padding:10px 18px; margin-bottom:10px; }
.band-title { font-weight:700; color:#1F3864; font-size:1.1rem; }
.band-sub   { color:#555; font-size:.85rem; }
.tipo-cort { background:#DEEAF1; padding:2px 8px; border-radius:4px; font-size:.8rem; font-weight:600; color:#1F3864; }
.tipo-alz  { background:#E2EFDA; padding:2px 8px; border-radius:4px; font-size:.8rem; font-weight:600; color:#375623; }
.tipo-pep  { background:#FCE4D6; padding:2px 8px; border-radius:4px; font-size:.8rem; font-weight:600; color:#C55A11; }
</style>
""", unsafe_allow_html=True)

# ── Carga ─────────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    camps = pd.read_excel(EXCEL, sheet_name="Campañas")
    cos   = pd.read_excel(EXCEL, sheet_name="Cosecheros_Campana")
    camps.columns = [c.replace("\n", " ") for c in camps.columns]
    cos.columns   = [c.replace("\n", " ") for c in cos.columns]
    for df in (camps, cos):
        for col in ("Inicio","Fin"):
            if col in df.columns:
                df[col] = pd.to_datetime(df[col])
    return camps, cos

camps, cos = load_data()
kg_col = next(c for c in camps.columns if "KG Total" in c and "Suelta" not in c)
TIPOS  = ["Cortador", "Alzador", "Pepeador"]
PLURAL = {"Cortador": "Cortadores", "Alzador": "Alzadores", "Pepeador": "Pepeadores"}

# ── Sidebar ───────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🌴 Hacienda La Ilusión SAS")
st.sidebar.markdown("**Cosecheros 2026**")
st.sidebar.markdown("---")
vista = st.sidebar.radio("Vista", ["📋  Campaña individual", "📊  Análisis general", "🏆  Campañas"],
                         label_visibility="collapsed")


# ═══════════════════════════════════════════════════════════════════════════════
# VISTA 1 — CAMPAÑA INDIVIDUAL
# ═══════════════════════════════════════════════════════════════════════════════
if "individual" in vista:

    st.sidebar.markdown("**Seleccionar campaña**")
    zona_sel = st.sidebar.selectbox("Zona", sorted(camps["Zona"].dropna().unique()))
    lote_sel = st.sidebar.selectbox("Lote",
        sorted(camps[camps["Zona"]==zona_sel]["Lote"].dropna().unique()))
    camp_lote = camps[(camps["Zona"]==zona_sel)&(camps["Lote"]==lote_sel)].sort_values("Campaña")

    opt_labels = [f"Campaña {int(r['Campaña'])}: "
                  f"{pd.Timestamp(r['Inicio']).strftime('%d %b')} → "
                  f"{pd.Timestamp(r['Fin']).strftime('%d %b %Y')}"
                  for _, r in camp_lote.iterrows()]
    opt_ids = [int(r["Campaña"]) for _, r in camp_lote.iterrows()]
    camp_id = opt_ids[opt_labels.index(st.sidebar.selectbox("Campaña", opt_labels))]

    camp_row = camp_lote[camp_lote["Campaña"]==camp_id].iloc[0]
    cos_camp_raw = (cos[(cos["Lote"]==lote_sel)&(cos["Campaña ID"]==camp_id)]
                   .sort_values(["Tipo Labor","KG Total"], ascending=[True,False])
                   .reset_index(drop=True))
    tipos_en_camp = [t for t in TIPOS if t in cos_camp_raw["Tipo Labor"].unique()]
    st.sidebar.markdown("**Tipo de trabajador**")
    tipos_sel = st.sidebar.multiselect("Tipo", tipos_en_camp, default=tipos_en_camp,
                                        label_visibility="collapsed")
    cos_camp = cos_camp_raw[cos_camp_raw["Tipo Labor"].isin(tipos_sel)].reset_index(drop=True)

    # ── encabezado ──────────────────────────────────────────────────────────
    zcol = Z_COL.get(zona_sel, DARK)
    ini  = pd.Timestamp(camp_row["Inicio"]).strftime("%d %b")
    fin  = pd.Timestamp(camp_row["Fin"]).strftime("%d %b %Y")
    dur  = int(camp_row["Duración (días)"])
    st.markdown(f"""
    <div class="band">
      <span style="color:{zcol};font-weight:700">{zona_sel}</span> &nbsp;·&nbsp;
      <span class="band-title">{lote_sel}</span> &nbsp;·&nbsp;
      <span class="band-sub">Campaña {camp_id} &nbsp;|&nbsp; {ini} → {fin} &nbsp;|&nbsp; {dur} días</span>
    </div>""", unsafe_allow_html=True)

    # ── KPIs ────────────────────────────────────────────────────────────────
    kg_tot   = float(camp_row[kg_col])
    n_cort   = int(camp_row.get("# Cort.", 0) or 0)
    n_alz    = int(camp_row.get("# Alz.",  0) or 0)
    n_pep    = int(camp_row.get("# Pep.",  0) or 0)
    j_cort   = int(camp_row.get("Jorn. Cort.", 0) or 0)
    j_alz    = int(camp_row.get("Jorn. Alz.",  0) or 0)
    kg_jorn  = float(camp_row.get("KG/Jornal Cort.", 0) or 0)
    kg_jorn_alz = camp_row.get("KG/Jornal Alz.", None)
    has_jorn = float(camp_row.get("Has/Jornal Cort.", 0) or 0)
    ciclo    = camp_row.get("Ciclo Prom", np.nan)
    score    = camp_row.get("Score (0-100)", None)
    grado    = camp_row.get("Grado", None)
    GRADE_CSS = {"A": "background:#375623;color:white", "B": "background:#70AD47;color:white",
                 "C": "background:#FFBF00;color:#1F3864", "D": "background:#C00000;color:white"}
    grade_style = GRADE_CSS.get(str(grado) if pd.notna(grado) else "", "")
    score_html = (f'<div style="font-size:1.6rem;font-weight:700;line-height:1">{int(score)}</div>'
                  f'<div style="font-size:1rem;font-weight:700;padding:2px 8px;border-radius:4px;'
                  f'display:inline-block;margin-top:2px;{grade_style}">{grado}</div>'
                  if pd.notna(score) else '<div class="kpi-val">—</div>')

    c1,c2,c3,c4,c5,c6,c7,c8 = st.columns(8)
    for col, lbl, val, css in [
        (c1, "KG Cosechados",    f"{kg_tot:,.0f}",     "kpi"),
        (c2, "Cortadores",       str(n_cort),           "kpi kpi-cort"),
        (c3, "Alzadores",        str(n_alz),            "kpi kpi-alz"),
        (c4, "Pepeadores",       str(n_pep),            "kpi kpi-pep"),
        (c5, "Jornales Cort.",   str(j_cort),           "kpi kpi-cort"),
        (c6, "KG/Jornal Cort.",  f"{kg_jorn:,.0f}",    "kpi"),
        (c7, "Ciclo Fruta",      f"{ciclo:.0f} d" if pd.notna(ciclo) else "—", "kpi"),
    ]:
        col.markdown(f'<div class="{css}"><div class="kpi-val">{val}</div>'
                     f'<div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)
    c8.markdown(f'<div class="kpi">{score_html}<div class="kpi-lbl">Calificación</div></div>',
                unsafe_allow_html=True)

    st.markdown("")

    # ── Tabla por tipo + Gráfico ─────────────────────────────────────────────
    col_tbl, col_cht = st.columns([54, 46])

    with col_tbl:
        st.markdown("#### Por cosechero")
        for tipo in ["Cortador", "Alzador", "Pepeador"]:
            sub = cos_camp[cos_camp["Tipo Labor"]==tipo].reset_index(drop=True)
            if sub.empty:
                continue
            badge = f'<span class="tipo-{tipo.lower()}">{PLURAL[tipo]} ({len(sub)})</span>'
            st.markdown(badge, unsafe_allow_html=True)
            total_kg = sub["KG Total"].sum()
            disp = sub[["Cosechero","KG Total","Días Trabajados","KG/Día"]].copy()
            disp.insert(0, "#", range(1, len(disp)+1))
            disp["% Total"] = (disp["KG Total"]/total_kg*100).round(1)
            has_col = "Has/Jornal" if "Has/Jornal" in sub.columns else None
            if has_col:
                disp["Has/Jornal"] = sub[has_col].apply(
                    lambda x: f"{x:.2f}" if pd.notna(x) else "")
            disp["KG Total"] = disp["KG Total"].apply(lambda x: f"{x:,.0f}")
            disp["KG/Día"]   = disp["KG/Día"].apply(lambda x: f"{x:,.0f}")
            disp["% Total"]  = disp["% Total"].apply(lambda x: f"{x:.0f}%")
            cols_show = ["#","Cosechero","KG Total","Días Trabajados","KG/Día","% Total"]
            if has_col:
                cols_show.append("Has/Jornal")
            st.dataframe(disp[cols_show], use_container_width=True, hide_index=True)
            tot_str = f"Total {PLURAL[tipo].lower()}: **{total_kg:,.0f} kg** · {sub['Días Trabajados'].sum()} jornales"
            if tipo == "Cortador":
                tot_str += f" · KG/jorn: **{kg_jorn:,.0f}** · Has/jornal: **{has_jorn:.2f}**"
            elif tipo == "Alzador" and pd.notna(kg_jorn_alz):
                has_jorn_alz_val = camp_row.get("Has/Jornal Alz.", None)
                tot_str += f" · KG/jorn alz: **{float(kg_jorn_alz):,.0f}**"
                if pd.notna(has_jorn_alz_val):
                    tot_str += f" · Has/jornal: **{float(has_jorn_alz_val):.2f}**"
            st.caption(tot_str)

    with col_cht:
        st.markdown("#### KG / Día por tipo de labor")

        # promedios hacienda por tipo
        cos_h = {}
        for t in TIPOS:
            sub_h = cos[cos["Tipo Labor"]==t]
            if len(sub_h):
                cos_h[t] = sub_h["KG Total"].sum() / sub_h["Días Trabajados"].sum()

        tipos_presentes = [t for t in TIPOS if not cos_camp[cos_camp["Tipo Labor"]==t].empty]
        n_tipos = len(tipos_presentes)
        fig, axes = plt.subplots(1, n_tipos, figsize=(5.5, max(3, 0.4*len(cos_camp)+0.6)),
                                 sharey=False)
        if n_tipos == 1:
            axes = [axes]
        fig.patch.set_facecolor("white")

        for ax_i, (ax, tipo) in enumerate(zip(axes, tipos_presentes)):
            sub = cos_camp[cos_camp["Tipo Labor"]==tipo].sort_values("KG Total", ascending=False)
            if sub.empty:
                ax.set_visible(False); continue
            vals  = sub["KG/Día"].tolist()
            names = [" ".join(n.split()[:2]) for n in sub["Cosechero"]]
            yp    = np.arange(len(vals))
            col_t = T_COL[tipo]
            ax.barh(yp, vals, color=col_t, edgecolor="white", alpha=0.85, height=0.65)
            vmax = max(vals) if vals else 1
            for yi, v in enumerate(vals):
                ax.text(v + vmax*0.02, yi, f"{v:,.0f}", va="center", fontsize=7.5, color="#333")
            if tipo in cos_h:
                ax.axvline(cos_h[tipo], color=DARK, linestyle="--", linewidth=1,
                           label=f"Hda: {cos_h[tipo]:,.0f}")
            ax.set_yticks(yp); ax.set_yticklabels(names, fontsize=7.5)
            ax.set_title(PLURAL[tipo], fontsize=9, fontweight="bold", color=col_t)
            ax.set_xlabel("KG/día", fontsize=8)
            ax.spines[["top","right"]].set_visible(False)
            ax.xaxis.grid(True, color=LGRAY, linestyle="--", linewidth=0.5, zorder=0)
            ax.set_axisbelow(True); ax.tick_params(left=False)
            ax.legend(fontsize=7, frameon=False, loc="lower right")

        plt.tight_layout(pad=0.5)
        st.pyplot(fig, use_container_width=True); plt.close(fig)

    # ── historial del lote ───────────────────────────────────────────────────
    with st.expander("📈 Historial de campañas en este lote"):
        hist = camp_lote.copy()
        hist["ini_str"] = hist["Inicio"].dt.strftime("%d/%m")
        n_camp = len(hist)
        fig2, axes2 = plt.subplots(1, 3, figsize=(11, 3))
        fig2.patch.set_facecolor("white")
        zcol_bar = [zcol if int(r["Campaña"])==camp_id else "#BBBBBB" for _,r in hist.iterrows()]
        for ax2, col2, tit in zip(axes2,
            [kg_col, "KG/Jornal Cort.", "# Cort."],
            ["KG Total", "KG/Jornal Cortadores", "# Cortadores"]):
            if col2 not in hist.columns:
                ax2.set_visible(False); continue
            ax2.bar(range(n_camp), hist[col2], color=zcol_bar, edgecolor="white")
            ax2.set_xticks(range(n_camp))
            ax2.set_xticklabels([f"C{int(r['Campaña'])}\n{r['ini_str']}"
                                  for _,r in hist.iterrows()], fontsize=7)
            ax2.set_title(tit, fontsize=9, fontweight="bold")
            ax2.spines[["top","right"]].set_visible(False)
            ax2.yaxis.grid(True, color=LGRAY, linestyle="--", linewidth=0.5, zorder=0)
            ax2.set_axisbelow(True)
        plt.tight_layout(pad=0.4)
        st.pyplot(fig2, use_container_width=True); plt.close(fig2)

    st.caption("Hacienda La Ilusión SAS · Datos 2026 · [C] Cortador  [A] Alzador  [P] Pepeador")


# ═══════════════════════════════════════════════════════════════════════════════
# VISTA 2 — ANÁLISIS GENERAL
# ═══════════════════════════════════════════════════════════════════════════════
elif "Análisis" in vista:
    st.title("Análisis General de Cosecheros — 2026")

    zonas_all = sorted(cos["Zona"].dropna().unique())
    tipos_all = [t for t in TIPOS if t in cos["Tipo Labor"].unique()]
    zona_f  = st.sidebar.multiselect("Zonas",  zonas_all, default=zonas_all)
    tipo_f  = st.sidebar.multiselect("Tipo de labor", tipos_all, default=tipos_all)
    fecha_min2 = cos["Inicio"].min().date()
    fecha_max2 = cos["Inicio"].max().date()
    fechas_f2  = st.sidebar.date_input("Rango de fechas", value=(fecha_min2, fecha_max2),
                                        min_value=fecha_min2, max_value=fecha_max2, key="f2")

    cos_f = cos[cos["Zona"].isin(zona_f) & cos["Tipo Labor"].isin(tipo_f)].copy() if zona_f and tipo_f else cos.copy()
    if isinstance(fechas_f2, (list, tuple)) and len(fechas_f2) == 2:
        f_ini2 = pd.Timestamp(fechas_f2[0]); f_fin2 = pd.Timestamp(fechas_f2[1])
        cos_f = cos_f[(cos_f["Inicio"] >= f_ini2) & (cos_f["Inicio"] <= f_fin2)]

    # ── KPIs globales ────────────────────────────────────────────────────────
    st.markdown("### Resumen hacienda")
    g_cols = st.columns(4)
    for col, (lbl, val) in zip(g_cols, [
        ("Cosecheros únicos",  f"{cos_f['Cosechero'].nunique()}"),
        ("Total jornales",     f"{cos_f['Días Trabajados'].sum():,}"),
        ("KG cosechados",      f"{cos_f['KG Total'].sum():,.0f}"),
        ("KG/Día promedio",    f"{cos_f['KG Total'].sum()/cos_f['Días Trabajados'].sum():,.0f}"),
    ]):
        col.markdown(f'<div class="kpi"><div class="kpi-val">{val}</div>'
                     f'<div class="kpi-lbl">{lbl}</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # ── KG/Día por zona Y tipo ───────────────────────────────────────────────
    st.markdown("### KG / Día por zona y tipo de labor")
    zona_tipo = (cos_f.groupby(["Zona","Tipo Labor"])
                 .agg(KG=("KG Total","sum"), Dias=("Días Trabajados","sum"))
                 .reset_index())
    zona_tipo["KG_dia"] = zona_tipo["KG"] / zona_tipo["Dias"]

    zonas_u = sorted(zona_tipo["Zona"].unique())
    x = np.arange(len(zonas_u))
    bw = 0.25
    offsets = {t: (i - (len(tipos_all)-1)/2)*bw for i, t in enumerate(tipos_all)}

    fig_z, ax_z = plt.subplots(figsize=(7, 4))
    fig_z.patch.set_facecolor("white")
    for tipo in tipos_all:
        sub_t = zona_tipo[zona_tipo["Tipo Labor"]==tipo]
        vals_t = [sub_t[sub_t["Zona"]==z]["KG_dia"].values[0]
                  if z in sub_t["Zona"].values else 0 for z in zonas_u]
        bars = ax_z.bar(x + offsets[tipo], vals_t, bw, label=tipo,
                        color=T_COL[tipo], edgecolor="white", alpha=0.88)
        for xi, v in enumerate(vals_t):
            if v > 0:
                ax_z.text(xi + offsets[tipo], v + 15, f"{v:,.0f}",
                          ha="center", fontsize=7.5, fontweight="bold", color=T_COL[tipo])

    avg_total = cos_f["KG Total"].sum() / cos_f["Días Trabajados"].sum()
    ax_z.axhline(avg_total, color=DARK, linestyle="--", linewidth=1.3,
                 label=f"Prom. total: {avg_total:,.0f}")
    ax_z.set_xticks(x); ax_z.set_xticklabels(zonas_u)
    ax_z.set_ylabel("KG / Día"); ax_z.legend(fontsize=8, frameon=False)
    ax_z.spines[["top","right"]].set_visible(False)
    ax_z.yaxis.grid(True, color=LGRAY, linestyle="--", linewidth=0.5, zorder=0)
    ax_z.set_axisbelow(True); ax_z.tick_params(bottom=False)
    plt.tight_layout(pad=0.4)
    st.pyplot(fig_z, use_container_width=True); plt.close(fig_z)

    # ── Ranking separado por tipo ────────────────────────────────────────────
    st.markdown("### Ranking por tipo de labor")
    tabs = st.tabs([f"🔵 Cortadores", "🟢 Alzadores", "🟠 Pepeadores"])

    for tab, tipo in zip(tabs, TIPOS):
        with tab:
            sub_t = cos_f[cos_f["Tipo Labor"]==tipo]
            if sub_t.empty:
                st.info(f"No hay datos de {PLURAL[tipo].lower()} con los filtros seleccionados.")
                continue
            rank = (sub_t.groupby(["Cosechero","Zona"])
                    .agg(KG_total=("KG Total","sum"),
                         Dias=("Días Trabajados","sum"),
                         Campanas=("Campaña ID","nunique"))
                    .reset_index())
            rank["KG_dia"] = (rank["KG_total"] / rank["Dias"]).round(0)
            rank = rank.sort_values("KG_dia", ascending=False).reset_index(drop=True)
            rank.index += 1
            avg_tipo = rank["KG_total"].sum() / rank["Dias"].sum()

            c_rank, c_slide = st.columns([3,1])
            with c_slide:
                n_top = st.slider(f"Top N", 5, min(40, len(rank)), 15, key=f"n_{tipo}")
            top_n = rank.head(n_top).sort_values("KG_dia")

            fig_r, ax_r = plt.subplots(figsize=(7, max(3, n_top*0.38)))
            fig_r.patch.set_facecolor("white")
            yp = np.arange(len(top_n))
            col_r = [Z_COL.get(z, DARK) for z in top_n["Zona"]]
            ax_r.barh(yp, top_n["KG_dia"], color=col_r, edgecolor="white",
                      alpha=0.85, height=0.7)
            for yi, (_, r) in enumerate(top_n.iterrows()):
                ax_r.text(r["KG_dia"] + max(top_n["KG_dia"])*0.01, yi,
                          f"{r['KG_dia']:,.0f}", va="center", fontsize=7.5)
            ax_r.axvline(avg_tipo, color=T_COL[tipo], linestyle="--", linewidth=1.3,
                         label=f"Prom. {PLURAL[tipo].lower()}: {avg_tipo:,.0f}")
            names_r = [" ".join(n.split()[:2]) for n in top_n["Cosechero"]]
            ax_r.set_yticks(yp); ax_r.set_yticklabels(names_r, fontsize=8)
            ax_r.set_xlabel("KG por día promedio")
            ax_r.set_title(f"Top {n_top} {PLURAL[tipo].lower()} por KG/día", fontweight="bold")
            ax_r.spines[["top","right"]].set_visible(False)
            ax_r.xaxis.grid(True, color=LGRAY, linestyle="--", linewidth=0.5, zorder=0)
            ax_r.set_axisbelow(True); ax_r.tick_params(left=False)
            handles_r = [mpatches.Patch(color=Z_COL[z], label=z)
                         for z in zonas_all if z in top_n["Zona"].values]
            handles_r.append(Line2D([0],[0], color=T_COL[tipo], linestyle="--",
                                    label=f"Prom.: {avg_tipo:,.0f}"))
            ax_r.legend(handles=handles_r, fontsize=7.5, loc="lower right", frameon=False)
            plt.tight_layout(pad=0.4)
            st.pyplot(fig_r, use_container_width=True); plt.close(fig_r)

            with st.expander("Ver tabla completa"):
                disp_r = rank.reset_index().rename(columns={
                    "index":"#","KG_total":"KG Total","Dias":"Días","Campanas":"Campañas","KG_dia":"KG/Día"})
                disp_r["KG Total"] = disp_r["KG Total"].apply(lambda x: f"{x:,.0f}")
                disp_r["KG/Día"]   = disp_r["KG/Día"].apply(lambda x: f"{x:,.0f}")
                st.dataframe(disp_r[["#","Cosechero","Zona","Campañas","Días","KG Total","KG/Día"]],
                             use_container_width=True, hide_index=True)

    st.caption("Hacienda La Ilusión SAS · Datos 2026 · Fuente: CosechaJulio25-Mayo26.xlsx")


# ═══════════════════════════════════════════════════════════════════════════════
# VISTA 3 — CALIFICACIÓN DE CAMPAÑAS
# ═══════════════════════════════════════════════════════════════════════════════
else:
    st.title("Calificación de Campañas — 2026")
    st.caption("Score 0-100: Ciclo de fruta 60% (óptimo ≤20d) + Rendimiento cortadores 40% (óptimo 4 t/ha)")

    score_col  = "Score (0-100)" if "Score (0-100)" in camps.columns else \
                 next((c for c in camps.columns if "Score" in c), None)
    grado_col  = "Grado" if "Grado" in camps.columns else None
    ciclo_col  = next((c for c in camps.columns if "Ciclo" in c and "Prom" in c), None)
    kg_ha_col  = "KG/HA" if "KG/HA" in camps.columns else None

    # filtros sidebar
    zonas_all3 = sorted(camps["Zona"].dropna().unique())
    zona_f3    = st.sidebar.multiselect("Zonas", zonas_all3, default=zonas_all3)
    fecha_min3 = camps["Inicio"].min().date()
    fecha_max3 = camps["Inicio"].max().date()
    fechas_f3  = st.sidebar.date_input("Rango de fechas", value=(fecha_min3, fecha_max3),
                                        min_value=fecha_min3, max_value=fecha_max3, key="f3")
    GRADE_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
    GRADE_CSS3  = {"A": "#375623", "B": "#70AD47", "C": "#FFBF00", "D": "#C00000"}

    camps_f = camps[camps["Zona"].isin(zona_f3)].copy() if zona_f3 else camps.copy()
    if isinstance(fechas_f3, (list, tuple)) and len(fechas_f3) == 2:
        f_ini3 = pd.Timestamp(fechas_f3[0]); f_fin3 = pd.Timestamp(fechas_f3[1])
        camps_f = camps_f[(camps_f["Inicio"] >= f_ini3) & (camps_f["Inicio"] <= f_fin3)]

    if score_col and grado_col:
        camps_f["_grade_ord"] = camps_f[grado_col].map(GRADE_ORDER).fillna(9)
        camps_f = camps_f.sort_values(["_grade_ord", score_col], ascending=[True, False])

    # KPIs resumen
    kp1, kp2, kp3, kp4 = st.columns(4)
    if score_col:
        avg_score = camps_f[score_col].mean()
        kp1.markdown(f'<div class="kpi"><div class="kpi-val">{avg_score:.0f}</div>'
                     f'<div class="kpi-lbl">Score promedio</div></div>', unsafe_allow_html=True)
    if grado_col:
        for g, c_ in zip(["A","B"], [kp2, kp3]):
            n = (camps_f[grado_col] == g).sum()
            c_.markdown(f'<div class="kpi"><div class="kpi-val">{n}</div>'
                        f'<div class="kpi-lbl">Grado {g}</div></div>', unsafe_allow_html=True)
        n_d = (camps_f[grado_col] == "D").sum()
        kp4.markdown(f'<div class="kpi"><div class="kpi-val">{n_d}</div>'
                     f'<div class="kpi-lbl">Grado D (crítico)</div></div>', unsafe_allow_html=True)

    st.markdown("")

    # Gráfico score por campaña (top / bottom)
    if score_col and grado_col:
        col_cht3, col_tbl3 = st.columns([50, 50])
        with col_cht3:
            st.markdown("#### Distribución de scores")
            fig_s, ax_s = plt.subplots(figsize=(6, 3.5))
            fig_s.patch.set_facecolor("white")
            grade_counts = camps_f[grado_col].value_counts().reindex(["A","B","C","D"]).fillna(0)
            bars = ax_s.bar(grade_counts.index, grade_counts.values,
                            color=[GRADE_CSS3.get(g,"#ccc") for g in grade_counts.index],
                            edgecolor="white", alpha=0.9)
            for bar, v in zip(bars, grade_counts.values):
                if v > 0:
                    ax_s.text(bar.get_x()+bar.get_width()/2, v+0.3, int(v),
                              ha="center", fontsize=10, fontweight="bold")
            ax_s.set_ylabel("# Campañas"); ax_s.set_xlabel("Grado")
            ax_s.spines[["top","right"]].set_visible(False)
            ax_s.yaxis.grid(True, color=LGRAY, linestyle="--", linewidth=0.5, zorder=0)
            ax_s.set_axisbelow(True); ax_s.tick_params(bottom=False)
            plt.tight_layout(pad=0.4)
            st.pyplot(fig_s, use_container_width=True); plt.close(fig_s)

        with col_tbl3:
            st.markdown("#### Score por zona")
            if ciclo_col:
                zona_score = camps_f.groupby("Zona").agg(
                    Score_prom=(score_col,"mean"),
                    Ciclo_prom=(ciclo_col,"mean"),
                    Campanas=("Zona","count")
                ).round(1).reset_index()
                zona_score["Score_prom"] = zona_score["Score_prom"].round(0).astype(int)
                st.dataframe(zona_score, use_container_width=True, hide_index=True)

    st.markdown("#### Ranking de campañas")
    cols_show3 = ["Zona","Lote","Campaña","Inicio","Fin"]
    if ciclo_col:       cols_show3.append(ciclo_col)
    if kg_ha_col:       cols_show3.append(kg_ha_col)
    if score_col:       cols_show3.append(score_col)
    if grado_col:       cols_show3.append(grado_col)
    cols_show3 = [c for c in cols_show3 if c in camps_f.columns]

    disp3 = camps_f[cols_show3].copy().reset_index(drop=True)
    disp3.index += 1
    for dc in ("Inicio","Fin"):
        if dc in disp3.columns:
            disp3[dc] = pd.to_datetime(disp3[dc]).dt.strftime("%d/%m/%Y")
    if ciclo_col and ciclo_col in disp3.columns:
        disp3[ciclo_col] = disp3[ciclo_col].apply(
            lambda x: f"{x:.1f} d" if pd.notna(x) else "—")
    if kg_ha_col and kg_ha_col in disp3.columns:
        disp3[kg_ha_col] = disp3[kg_ha_col].apply(
            lambda x: f"{x:,.0f}" if pd.notna(x) else "—")

    st.dataframe(disp3, use_container_width=True)
    st.caption("Hacienda La Ilusión SAS · Datos 2026 · Score: Ciclo 60% + Rendto Cort. 40%")
