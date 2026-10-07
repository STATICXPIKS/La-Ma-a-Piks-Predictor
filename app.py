import os
import gradio as gr
from datos import *
from motores import *

def cambiar_estado(idx, est):
    try:
        requests.patch(f"{SUPABASE_URL}/rest/v1/historial_picks?id=eq.{int(idx)}", headers=SUPABASE_HEADERS, json={"estado": est}, timeout=5)
    except Exception: pass
    recalibrar_modelos_auto()
    return cargar_dashboard()

def cargar_dashboard():
    stats, tw, tl, tg, pct = calcular_metricas_historial()
    hist = cargar_historial_db()
    pend = [x for x in hist if x.get("estado") == "PENDING"]
    wins = [x for x in hist if x.get("estado") == "WIN"]
    loss = [x for x in hist if x.get("estado") == "LOSS"]

    return (
        f"<h2 style='color:#059669; text-align:center;'>EFECTIVIDAD GLOBAL: {pct}% ({tw}W / {tl}L)</h2>",
        f"⏳ <b>PENDIENTES ({len(pend)})</b><br/>" + "<br/>".join([f"• #{x.get('id','?')} {x.get('partido','')} - {x.get('seleccion','')}" for x in reversed(pend[:10])]),
        f"✅ <b>GANADAS ({len(wins)})</b><br/>" + "<br/>".join([f"• #{x.get('id','?')} {x.get('partido','')} - {x.get('seleccion','')}" for x in reversed(wins[:10])]),
        f"❌ <b>PERDIDAS ({len(loss)})</b><br/>" + "<br/>".join([f"• #{x.get('id','?')} {x.get('partido','')} - {x.get('seleccion','')}" for x in reversed(loss[:10])])
    )

with gr.Blocks(title="La Maña Picks", theme=gr.themes.Soft(primary_hue="emerald")) as app:
    gr.Markdown("# ⚽ LA MAÑA PICKS • MOTOR MULTIVARIABLE DE APUESTAS")
    
    with gr.Row():
        btn_win = gr.Button("✅ Marcar WIN por ID")
        num_id = gr.Number(value=1, label="ID Pick", precision=0)
        btn_loss = gr.Button("❌ Marcar LOSS por ID")

    dash_head = gr.HTML()
    with gr.Row():
        out_p = gr.HTML()
        out_w = gr.HTML()
        out_l = gr.HTML()

    gr.Markdown("---")
    gr.Markdown("### ⚽ ANÁLISIS MULTIVARIABLE DE FÚTBOL (9 GRUPOS)")

    with gr.Row():
        d_liga = gr.Dropdown(choices=list(ESPN_SOCCER_LEAGUES.keys()), value="Premier League", label="Liga")
        d_loc = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Arsenal", label="Local")
        d_vis = gr.Dropdown(choices=list(PREMIER_DICT.keys()), value="Chelsea", label="Visitante")

    with gr.Row():
        xg_lc = gr.Number(value=1.95, label="xG Local (Casa)")
        xga_lc = gr.Number(value=0.85, label="xGA Concedido Local")
        xg_vf = gr.Number(value=1.45, label="xG Visitante (Fuera)")
        xga_vf = gr.Number(value=1.30, label="xGA Concedido Visitante")

    with gr.Row():
        p5_l = gr.Number(value=11.0, label="Pts ult 5 Local")
        p5_v = gr.Number(value=7.0, label="Pts ult 5 Visitante")
        st_l = gr.Number(value=5.5, label="Tiros Puerta Local")
        bc_v = gr.Number(value=2.1, label="Grandes Ocasiones Concedidas Vis")

    with gr.Row():
        bj_l = gr.Number(value=1, label="Bajas Local")
        bj_v = gr.Number(value=2, label="Bajas Visitante")
        des_l = gr.Number(value=6.0, label="Dias Descanso Local")
        des_v = gr.Number(value=3.0, label="Dias Descanso Visitante")
        dt_l = gr.Dropdown(choices=["No", "Sí"], value="No", label="¿Efecto DT Nuevo?")

    with gr.Row():
        c_l = gr.Number(value=1.85, label="Cuota Local")
        c_e = gr.Number(value=3.60, label="Cuota Empate")
        c_v = gr.Number(value=4.20, label="Cuota Visitante")
        c_btts_s = gr.Number(value=1.80, label="Cuota BTTS Sí")
        c_btts_n = gr.Number(value=1.95, label="Cuota BTTS No")

    with gr.Row():
        c_o15 = gr.Number(value=1.28, label="Cuota Over 1.5")
        c_o25 = gr.Number(value=1.85, label="Cuota Over 2.5")
        c_o35 = gr.Number(value=3.20, label="Cuota Over 3.5")
        c_u25 = gr.Number(value=1.95, label="Cuota Under 2.5")
        c_ht = gr.Number(value=1.40, label="Cuota Over 0.5 HT")

    btn_sim = gr.Button("🚀 Simular Partido (9 Grupos)", variant="primary")
    out_html = gr.HTML()

    st_p1, st_p2, st_p3, st_p4, st_p5, st_m = gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State(""), gr.State("")

    btn_sim.click(
        fn=simular_futbol_9grupos,
        inputs=[d_liga, d_loc, d_vis, xg_lc, xga_lc, xg_vf, xga_vf, p5_l, p5_v, st_l, bc_v, bj_l, bj_v, des_l, des_v, dt_l, c_l, c_e, c_v, c_btts_s, c_btts_n, c_o15, c_o25, c_o35, c_u25, c_ht, gr.State(PREMIER_DICT)],
        outputs=[out_html, st_p1, st_p2, st_p3, st_p4, st_p5, st_m]
    )

    btn_win.click(fn=lambda idx: cambiar_estado(idx, "WIN"), inputs=[num_id], outputs=[dash_head, out_p, out_w, out_l])
    btn_loss.click(fn=lambda idx: cambiar_estado(idx, "LOSS"), inputs=[num_id], outputs=[dash_head, out_p, out_w, out_l])

    app.load(fn=cargar_dashboard, outputs=[dash_head, out_p, out_w, out_l])

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    is_colab = "COLAB_GPU" in os.environ or "GGL_SUPPRESS_SANDBOX_CHECK" in os.environ
    app.launch(share=is_colab, server_name="0.0.0.0", server_port=port)
