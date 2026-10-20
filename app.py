import os
import gradio as gr
from nhl_model import ejecutar_modelo_nhl_completo

# INTERFAZ PARA EJECUTAR MODELO NHL EN VIVO
with gr.Blocks(title="La Maña Picks - NHL Model") as app_mana:
    gr.Markdown("# 🏒 **La Maña Picks • Modelo Cuantitativo NHL (NASH IA)**")
    gr.Markdown("Análisis estadístico automatizado con métricas avanzadas (xG, Corsi, Fenwick, Porteros, B2B y Monte Carlo).")
    
    with gr.Row():
        with gr.Column():
            eq_loc = gr.Textbox(value="Florida Panthers", label="Equipo Local")
            eq_vis = gr.Textbox(value="Edmonton Oilers", label="Equipo Visitante")
            
            with gr.Row():
                c_ml_l = gr.Number(value=1.85, label="Cuota ML Local")
                c_ml_v = gr.Number(value=1.95, label="Cuota ML Visitante")
                
            with gr.Row():
                c_pl_l = gr.Number(value=2.85, label="Cuota Puck Line Local (-1.5)")
                c_pl_v = gr.Number(value=1.45, label="Cuota Puck Line Visitante (+1.5)")

            with gr.Row():
                lin_tot = gr.Number(value=6.0, label="Línea Total Goles")
                c_ov = gr.Number(value=1.90, label="Cuota Over")
                c_un = gr.Number(value=1.90, label="Cuota Under")

            btn_sim = gr.Button("Ejecutar Análisis NHL y Enviar Pick a Netlify 🚀", variant="primary")
            
        with gr.Column():
            out_res = gr.JSON(label="Resultados del Modelo (Monte Carlo 10K)")

    btn_sim.click(
        fn=lambda loc, vis, ml_l, ml_v, pl_l, pl_v, tot, ov, un: ejecutar_modelo_nhl_completo(
            loc_nombre=loc, vis_nombre=vis,
            cuota_ml_loc=ml_l, cuota_ml_vis=ml_v,
            linea_pl_loc=-1.5, cuota_pl_loc=pl_l, linea_pl_vis=1.5, cuota_pl_vis=pl_v,
            linea_total=tot, cuota_over=ov, cuota_under=un,
            linea_sog=62.5, cuota_sog_over=1.85, cuota_sog_under=1.85
        ),
        inputs=[eq_loc, eq_vis, c_ml_l, c_ml_v, c_pl_l, c_pl_v, lin_tot, c_ov, c_un],
        outputs=[out_res]
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    app_mana.launch(server_name="0.0.0.0", server_port=port)
