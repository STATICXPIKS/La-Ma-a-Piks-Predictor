# Cálculo de cuotas justas
    cuota_j_ml_loc = round(100.0 / prob_ml_loc, 2) if prob_ml_loc > 0 else 2.0
    cuota_j_ml_vis = round(100.0 / prob_ml_vis, 2) if prob_ml_vis > 0 else 2.0
    cuota_j_pl_loc = round(100.0 / prob_pl_loc, 2) if prob_pl_loc > 0 else 2.0
    cuota_j_pl_vis = round(100.0 / prob_pl_vis, 2) if prob_pl_vis > 0 else 2.0
    cuota_j_over = round(100.0 / prob_over, 2) if prob_over > 0 else 2.0
    cuota_j_under = round(100.0 / prob_under, 2) if prob_under > 0 else 2.0

    # Clasificación de BET 🔥 y MAYBE ⚡ según % EV
    if ev_ml_loc >= 2.5:
        bet_principal = f"{loc_nombre} ML @ {cuota_ml_loc}"
        bet_ev = f"+{ev_ml_loc}%"
    elif ev_ml_vis >= 2.5:
        bet_principal = f"{vis_nombre} ML @ {cuota_ml_vis}"
        bet_ev = f"+{ev_ml_vis}%"
    elif ev_over >= 2.5:
        bet_principal = f"OVER {l_tot} Goles @ {cuota_over}"
        bet_ev = f"+{ev_over}%"
    else:
        bet_principal = f"{best_pick[1]}"
        bet_ev = f"+{max(0.1, best_pick[4])}%"

    # Selección secundaria / cobertura MAYBE ⚡
    if ev_pl_vis >= 0.5 and "ML" in bet_principal:
        maybe_principal = f"{vis_nombre} {linea_pl_vis:+g} @ {cuota_pl_vis}"
        maybe_ev = f"+{max(0.2, ev_pl_vis)}%"
    elif ev_under >= 0.5:
        maybe_principal = f"UNDER {l_tot} Goles @ {cuota_under}"
        maybe_ev = f"+{max(0.2, ev_under)}%"
    else:
        maybe_principal = f"{loc_nombre} {linea_pl_loc:+g} @ {cuota_pl_loc}"
        maybe_ev = f"+{max(0.1, ev_pl_loc)}%"

    resumen_texto = f"{loc_nombre} vs {vis_nombre}: Proyección de {lambda_loc:.2f} a {lambda_vis:.2f} goles (Total: {lambda_loc + lambda_vis:.2f}). La ventaja principal (+EV) detectada por FROST-IA recomienda enfocar el valor en {bet_principal}."

    return {
        "equipo_local_abbr": loc_st["abbr"].upper(),
        "equipo_visitante_abbr": vis_st["abbr"].upper(),
        "proyeccion_goles": f"{lambda_loc:.2f} - {lambda_vis:.2f}",
        "total_goles_proyectado": round(lambda_loc + lambda_vis, 2),
        "bet_fire": bet_principal,
        "bet_ev": bet_ev,
        "maybe_lightning": maybe_principal,
        "maybe_ev": maybe_ev,
        "ml_local": {"prob": prob_ml_loc, "cuota_justa": cuota_j_ml_loc},
        "ml_visitante": {"prob": prob_ml_vis, "cuota_justa": cuota_j_ml_vis},
        "pl_local": {"linea": linea_pl_loc, "prob": prob_pl_loc, "cuota_justa": cuota_j_pl_loc},
        "pl_visitante": {"linea": linea_pl_vis, "prob": prob_pl_vis, "cuota_justa": cuota_j_pl_vis},
        "total_over": {"linea": l_tot, "prob": prob_over, "cuota_justa": cuota_j_over},
        "total_under": {"linea": l_tot, "prob": prob_under, "cuota_justa": cuota_j_under},
        "resumen_explicado": resumen_texto
    }
