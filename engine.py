import numpy as np


def softmax(u):
    u = u - np.max(u)
    e = np.exp(u)
    return e / e.sum()


class MarketEngine:
    """
    Motor de simulador de marketing docente:
    - 3 segmentos
    - conocimiento acumulado y competitivo
    - posicionamiento de marca acumulado (value + premium)
    - comunicación por canal (en euros)
    - publicidad online con foco en compra
    - atributos de producto con impacto distinto por segmento
    - retención + captación
    - aprendizaje del mercado
    - eventos aleatorios
    - research con ruido
    - coherencia estratégica

    Regla de presupuesto:
    - El presupuesto de la ronda controla:
        * comunicación
        * promoción
        * distribución
        * inversión en producto
        * informes de investigación
    - El coste de fabricación NO consume presupuesto,
      pero SÍ afecta al beneficio.
    - El coste de almacenamiento del stock NO consume presupuesto
      de marketing, pero SÍ reduce el beneficio de la ronda.
    """

    MARKET_EVENTS = [
        "MARKET_GROWTH",
        "DEMAND_DROP",
        "AD_SATURATION",
        "CONSUMER_SENSITIVITY",
        "PROMO_SATURATION",
    ]

    TEAM_EVENTS = [
        "VIRAL_CAMPAIGN",
        "DISTRIBUTOR_DEAL",
        "BRAND_CRISIS",
        "PRODUCTION_PROBLEMS",
    ]

    # Coste de almacenamiento: 15% del coste unitario final por cada unidad sobrante.
    # Afecta al beneficio, no al presupuesto de marketing.
    STORAGE_COST_RATE = 0.15

    def __init__(self, team_names, seed=7):
        self.rng = np.random.default_rng(seed)
        self.teams = team_names
        self.B = len(team_names)

        # Segmentos
        self.seg_names = ["Ahorradores", "Equilibrados", "Exigentes"]
        self.seg_w = np.array([0.45, 0.35, 0.20])

        # Sensibilidades por segmento
        self.b_price = np.array([-3.0, -1.9, -1.0])
        self.b_dist = np.array([1.0, 1.1, 1.3])

        # Importancia de atributos de producto por segmento
        # Columnas: rendimiento, diseño, fiabilidad
        self.product_weights = np.array([
            [0.55, 0.15, 0.30],  # Ahorradores
            [0.35, 0.30, 0.35],  # Equilibrados
            [0.20, 0.45, 0.35],  # Exigentes
        ])

        # Base de retención por segmento
        self.base_retention = np.array([0.48, 0.60, 0.72])

        # Mercado
        self.t = 0
        self.market_base = 600_000
        self.season_periods = 12

        # Costes y preferencias iniciales
        self.unit_cost = self.rng.uniform(3.6, 4.4, size=self.B)
        self.base_pref = self.rng.normal(0.0, 0.35, size=(self.B, 3))

        # Decays / memoria
        self.aw_decay = 0.82
        self.brand_decay = 0.90
        self.perf_decay = 0.45

        # Stocks acumulados
        self.aw_adstock = np.zeros(self.B)
        self.brand_value = np.zeros(self.B)
        self.brand_premium = np.zeros(self.B)
        self.performance_stock = np.zeros(self.B)

        # Conocimiento inicial
        self.awareness = np.full(self.B, 0.20)

        # Aprendizaje del mercado / experiencia acumulada
        self.satisfaction = np.zeros(self.B)

        # Base de clientes del periodo anterior por marca y segmento
        self.customer_base = np.zeros((self.B, 3))
        # Stock acumulado por equipo de rondas anteriores.
        self.inventory = np.zeros(self.B)

        self._reset_round_modifiers()

    # -----------------------------
    # SERIALIZACIÓN DEL ESTADO
    # -----------------------------
    def get_state(self):
        return {
            "teams": self.teams,
            "B": self.B,
            "t": self.t,
            "unit_cost": self.unit_cost.tolist(),
            "base_pref": self.base_pref.tolist(),
            "aw_adstock": self.aw_adstock.tolist(),
            "brand_value": self.brand_value.tolist(),
            "brand_premium": self.brand_premium.tolist(),
            "performance_stock": self.performance_stock.tolist(),
            "awareness": self.awareness.tolist(),
            "satisfaction": self.satisfaction.tolist(),
            "customer_base": self.customer_base.tolist(),
            "inventory": self.inventory.tolist(),
            "rng_state": self.rng.bit_generator.state,
            # Modificadores temporales de evento.
            # Se guardan para permitir que el profesor genere un evento al abrir la ronda
            # y que ese mismo evento se aplique exactamente al cerrar la ronda.
            "round_modifiers": {
                "market_mult": float(getattr(self, "market_mult", 1.0)),
                "ad_effect_mult": float(getattr(self, "ad_effect_mult", 1.0)),
                "price_sens_mult": float(getattr(self, "price_sens_mult", 1.0)),
                "promo_effect_mult": float(getattr(self, "promo_effect_mult", 1.0)),
                "team_awareness_boost": getattr(self, "team_awareness_boost", np.zeros(self.B)).tolist(),
                "team_dist_mult": getattr(self, "team_dist_mult", np.ones(self.B)).tolist(),
                "team_unit_cost_mult": getattr(self, "team_unit_cost_mult", np.ones(self.B)).tolist(),
                "team_capacity_mult": getattr(self, "team_capacity_mult", np.ones(self.B)).tolist(),
            },
        }

    def set_state(self, state):
        self.t = int(state["t"])
        self.unit_cost = np.array(state["unit_cost"], dtype=float)
        self.base_pref = np.array(state["base_pref"], dtype=float)
        self.aw_adstock = np.array(state.get("aw_adstock", np.zeros(self.B)), dtype=float)
        self.brand_value = np.array(state.get("brand_value", np.zeros(self.B)), dtype=float)
        self.brand_premium = np.array(state.get("brand_premium", np.zeros(self.B)), dtype=float)
        self.performance_stock = np.array(state.get("performance_stock", np.zeros(self.B)), dtype=float)
        self.awareness = np.array(state.get("awareness", np.full(self.B, 0.20)), dtype=float)
        self.satisfaction = np.array(state.get("satisfaction", np.zeros(self.B)), dtype=float)
        self.customer_base = np.array(
            state.get("customer_base", np.zeros((self.B, 3))),
            dtype=float
        )
        self.inventory = np.array(state.get("inventory", np.zeros(self.B)), dtype=float)

        self.rng = np.random.default_rng()
        self.rng.bit_generator.state = state["rng_state"]

        self._reset_round_modifiers()
        modifiers = state.get("round_modifiers") or {}
        if modifiers:
            self.market_mult = float(modifiers.get("market_mult", self.market_mult))
            self.ad_effect_mult = float(modifiers.get("ad_effect_mult", self.ad_effect_mult))
            self.price_sens_mult = float(modifiers.get("price_sens_mult", self.price_sens_mult))
            self.promo_effect_mult = float(modifiers.get("promo_effect_mult", self.promo_effect_mult))
            self.team_awareness_boost = np.array(
                modifiers.get("team_awareness_boost", self.team_awareness_boost),
                dtype=float
            )
            self.team_dist_mult = np.array(
                modifiers.get("team_dist_mult", self.team_dist_mult),
                dtype=float
            )
            self.team_unit_cost_mult = np.array(
                modifiers.get("team_unit_cost_mult", self.team_unit_cost_mult),
                dtype=float
            )
            self.team_capacity_mult = np.array(
                modifiers.get("team_capacity_mult", self.team_capacity_mult),
                dtype=float
            )

    # -----------------------------
    # UTILIDADES
    # -----------------------------
    def _reset_round_modifiers(self):
        self.market_mult = 1.0
        self.ad_effect_mult = 1.0
        self.price_sens_mult = 1.0
        self.promo_effect_mult = 1.0
        self.team_awareness_boost = np.zeros(self.B)
        self.team_dist_mult = np.ones(self.B)
        self.team_unit_cost_mult = np.ones(self.B)
        self.team_capacity_mult = np.ones(self.B)

    def _team_idx(self, team_name):
        return self.teams.index(team_name)

    def _market_size_by_segment(self):
        season = 1.0 + 0.14 * np.sin(2 * np.pi * (self.t % self.season_periods) / self.season_periods)
        trend = 1.0 + 0.008 * self.t
        shock = np.exp(self.rng.normal(0.0, 0.05))
        total = self.market_base * season * trend * shock * self.market_mult
        return total * self.seg_w

    def _safe_mix(self, mix):
        trad = float(mix.get("trad", 0.0))
        online = float(mix.get("online", 0.0))
        rrss = float(mix.get("rrss", 0.0))
        pr = float(mix.get("pr", 0.0))

        total = trad + online + rrss + pr
        if total <= 0:
            return {"trad": 0.25, "online": 0.25, "rrss": 0.25, "pr": 0.25}

        return {
            "trad": trad / total,
            "online": online / total,
            "rrss": rrss / total,
            "pr": pr / total
        }

    def _strategy_coherence(
        self,
        price,
        quality,
        promo,
        effective_dist,
        online,
        trad,
        rrss,
        pr,
        brand_value_term,
        brand_premium_term,
        awareness_level
    ):
        """
        Devuelve:
        - coherence_term: efecto numérico a aplicar en consideración / utilidad
        - positioning_x: lectura de posicionamiento valor/precio
        - positioning_y: lectura de posicionamiento calidad
        """
        coherence = np.zeros_like(price)

        # 1) Precio alto sin calidad suficiente -> penalización fuerte
        quality_supported_price = 7.7 + 4.6 * quality
        coherence -= 0.28 * np.maximum(price - quality_supported_price, 0.0)

        # 2) Posicionamiento premium + promociones agresivas -> incoherencia
        premium_orientation = brand_premium_term > (brand_value_term + 0.03)
        coherence -= 1.10 * np.maximum(promo - 0.12, 0.0) * premium_orientation.astype(float)

        # 3) Captación fuerte con online pero poca distribución -> incoherencia
        online_pressure = np.log1p(online / 7000.0)
        dist_gap = np.maximum(0.58 - effective_dist, 0.0)
        coherence -= 0.22 * online_pressure * (1.0 + 2.0 * dist_gap)

        # 4) Mucho conocimiento pero poca presencia real -> frustración del mercado
        coherence -= 0.16 * np.maximum(awareness_level - effective_dist, 0.0)

        # 5) Estrategia de valor coherente: precio competitivo + cierta promoción
        coherence += 0.12 * np.maximum(8.2 - price, 0.0) * np.minimum(promo, 0.10)

        # 6) Estrategia premium coherente: PR / tradicional + buen producto + promo moderada
        premium_comm = np.log1p((0.65 * pr + 0.35 * trad) / 7000.0)
        coherence += 0.12 * premium_comm * np.maximum(quality - 0.58, 0.0)
        coherence -= 0.08 * np.maximum(0.50 - quality, 0.0)

        # 7) Mezcla extrema incoherente: muy barato pero muy premium
        coherence -= 0.12 * np.maximum(8.0 - price, 0.0) * premium_orientation.astype(float)

        # Acotar
        coherence = np.clip(coherence, -0.45, 0.35)

        # Lectura simple de posicionamiento
        positioning_x = np.clip(
            0.58 * np.maximum(0.0, 9.2 - price) / 3.0
            + 0.28 * np.clip(brand_value_term / 0.35, 0.0, 1.0)
            + 0.14 * np.minimum(promo / 0.15, 1.0),
            0.0,
            1.0
        )

        positioning_y = np.clip(
            0.55 * quality
            + 0.20 * np.clip(brand_premium_term / 0.35, 0.0, 1.0)
            + 0.10 * np.log1p(pr / 10000.0)
            + 0.08 * np.log1p(trad / 10000.0)
            - 0.08 * np.maximum(promo - 0.12, 0.0),
            0.0,
            1.0
        )

        return coherence, positioning_x, positioning_y

    # -----------------------------
    # EVENTOS
    # -----------------------------
    def random_event(self):
        self._reset_round_modifiers()

        event_scope = str(self.rng.choice(["market", "team"]))

        if event_scope == "market":
            event_key = str(self.rng.choice(self.MARKET_EVENTS))
            return self._apply_market_event(event_key)

        event_key = str(self.rng.choice(self.TEAM_EVENTS))
        team_name = self.teams[int(self.rng.integers(0, self.B))]
        return self._apply_team_event(event_key, team_name)

    def _apply_market_event(self, event_key):
        if event_key == "MARKET_GROWTH":
            bump = float(self.rng.uniform(1.08, 1.18))
            self.market_mult = bump
            return {
                "key": event_key,
                "title": "Crecimiento del mercado",
                "desc": "La categoría se expande y aumenta la demanda global en esta ronda.",
                "extra": f"Demanda total x{bump:.2f}"
            }

        if event_key == "DEMAND_DROP":
            drop = float(self.rng.uniform(0.82, 0.92))
            self.market_mult = drop
            return {
                "key": event_key,
                "title": "Caída de la demanda",
                "desc": "El mercado se contrae y se reduce el tamaño de la categoría en esta ronda.",
                "extra": f"Demanda total x{drop:.2f}"
            }

        if event_key == "AD_SATURATION":
            mult = float(self.rng.uniform(0.65, 0.82))
            self.ad_effect_mult = mult
            return {
                "key": event_key,
                "title": "Saturación publicitaria",
                "desc": "La comunicación pierde eficacia porque los consumidores están sobreexpuestos.",
                "extra": f"Efectividad de comunicación x{mult:.2f}"
            }

        if event_key == "CONSUMER_SENSITIVITY":
            mult = float(self.rng.uniform(1.12, 1.32))
            self.price_sens_mult = mult
            return {
                "key": event_key,
                "title": "Sensibilidad del consumidor",
                "desc": "El consumidor se vuelve más sensible al precio este periodo.",
                "extra": f"Sensibilidad al precio x{mult:.2f}"
            }

        if event_key == "PROMO_SATURATION":
            mult = float(self.rng.uniform(0.60, 0.80))
            self.promo_effect_mult = mult
            return {
                "key": event_key,
                "title": "Saturación de promociones",
                "desc": "Las promociones pierden impacto porque el mercado se acostumbra a ellas.",
                "extra": f"Efectividad promocional x{mult:.2f}"
            }

        return None

    def _apply_team_event(self, event_key, team_name):
        idx = self._team_idx(team_name)

        if event_key == "VIRAL_CAMPAIGN":
            bump = float(self.rng.uniform(0.08, 0.16))
            self.team_awareness_boost[idx] = bump
            return {
                "key": event_key,
                "title": "Campaña viral",
                "desc": "Un equipo consigue una campaña con gran visibilidad y gana notoriedad.",
                "extra": f"Afecta a {team_name} (+{bump:.0%} conocimiento)"
            }

        if event_key == "DISTRIBUTOR_DEAL":
            mult = float(self.rng.uniform(1.12, 1.28))
            self.team_dist_mult[idx] = mult
            return {
                "key": event_key,
                "title": "Acuerdo de distribuidor",
                "desc": "Un equipo amplía su cobertura comercial gracias a un acuerdo estratégico.",
                "extra": f"Afecta a {team_name} (distribución x{mult:.2f})"
            }

        if event_key == "BRAND_CRISIS":
            drop = float(self.rng.uniform(0.08, 0.16))
            self.team_awareness_boost[idx] = -drop
            self.satisfaction[idx] = max(self.satisfaction[idx] - 0.08, -0.6)
            self.brand_premium[idx] = max(self.brand_premium[idx] * 0.88, 0.0)
            return {
                "key": event_key,
                "title": "Crisis de marca",
                "desc": "Un equipo sufre una pérdida de imagen y baja su visibilidad en el mercado.",
                "extra": f"Afecta a {team_name} (-{drop:.0%} conocimiento)"
            }

        if event_key == "PRODUCTION_PROBLEMS":
            capacity = float(self.rng.uniform(0.70, 0.88))
            cost_mult = float(self.rng.uniform(1.06, 1.14))
            self.team_capacity_mult[idx] = capacity
            self.team_unit_cost_mult[idx] = cost_mult
            return {
                "key": event_key,
                "title": "Problemas de producción",
                "desc": "Un equipo sufre incidencias operativas que limitan sus ventas y elevan costes.",
                "extra": f"Afecta a {team_name} (capacidad x{capacity:.2f}, coste x{cost_mult:.2f})"
            }

        return None

    # -----------------------------
    # LECTURA DE COMUNICACIÓN
    # -----------------------------
    def _read_comm_channels(self, decisions):
        trad = np.zeros(self.B)
        online = np.zeros(self.B)
        rrss = np.zeros(self.B)
        pr = np.zeros(self.B)

        for i, t in enumerate(self.teams):
            d = decisions[t]

            if any(k in d for k in ["comm_trad", "comm_online", "comm_rrss", "comm_pr"]):
                trad[i] = float(d.get("comm_trad", 0.0))
                online[i] = float(d.get("comm_online", 0.0))
                rrss[i] = float(d.get("comm_rrss", 0.0))
                pr[i] = float(d.get("comm_pr", 0.0))
            else:
                comm_total = float(d.get("comm_total", d.get("ad_spend", 0.0)))
                mix = self._safe_mix(d.get("comm_mix", {
                    "trad": 0.25,
                    "online": 0.25,
                    "rrss": 0.25,
                    "pr": 0.25
                }))
                trad[i] = comm_total * mix["trad"]
                online[i] = comm_total * mix["online"]
                rrss[i] = comm_total * mix["rrss"]
                pr[i] = comm_total * mix["pr"]

        return trad, online, rrss, pr

    # -----------------------------
    # FUNNEL ESTIMADO DE MARCA
    # -----------------------------
    def estimate_brand_funnel_strength(self, team_name, decision):
        """
        Estima la fuerza prevista de la marca en el funnel para la pantalla
        de toma de decisiones. No ejecuta la ronda ni modifica el estado.

        Combina memoria de marca (awareness, adstock, satisfacción, base de
        clientes y posicionamiento acumulado) con la decisión que el equipo
        está diseñando para la próxima ronda.
        """
        idx = self._team_idx(team_name)

        def clip01(x):
            return float(np.clip(float(x), 0.0, 1.0))

        def log_strength(value, scale=10000.0, divisor=1.35):
            return clip01(np.log1p(max(float(value), 0.0) / scale) / divisor)

        price = float(decision.get("price", 8.0))
        promo = float(np.clip(decision.get("promo", 0.0), 0.0, 0.30))
        dist = float(np.clip(decision.get("distribution", 0.50), 0.05, 1.0))

        product_perf = float(np.clip(decision.get("product_perf", 0.50), 0.0, 1.0))
        product_design = float(np.clip(decision.get("product_design", 0.50), 0.0, 1.0))
        product_reliability = float(np.clip(decision.get("product_reliability", 0.50), 0.0, 1.0))
        quality = float(decision.get(
            "quality",
            0.40 * product_perf + 0.25 * product_design + 0.35 * product_reliability,
        ))
        quality = clip01(quality)

        trad = float(decision.get("comm_trad", 0.0))
        online = float(decision.get("comm_online", 0.0))
        rrss = float(decision.get("comm_rrss", 0.0))
        pr = float(decision.get("comm_pr", 0.0))

        prev_units_by_team = self.customer_base.sum(axis=1)
        prev_total_units = float(prev_units_by_team.sum())
        previous_share = (
            float(prev_units_by_team[idx] / prev_total_units)
            if prev_total_units > 0
            else 1.0 / max(float(self.B), 1.0)
        )
        previous_customers = float(prev_units_by_team[idx])
        previous_awareness = clip01(self.awareness[idx])
        satisfaction_memory = clip01(0.5 + 0.5 * np.clip(float(self.satisfaction[idx]), -0.6, 1.5) / 1.5)

        # Conocimiento: memoria de marca + presión de comunicación actual.
        awareness_input = (0.28 * trad + 0.24 * rrss + 0.16 * pr + 0.12 * online) * self.ad_effect_mult
        projected_aw_adstock = 0.72 * float(self.aw_adstock[idx]) + awareness_input
        current_comm_strength = log_strength(projected_aw_adstock, scale=10000.0, divisor=1.35)
        retention_memory = clip01(0.65 * satisfaction_memory + 0.35 * min(previous_customers / 90000.0, 1.0))

        knowledge = clip01(
            0.46 * previous_awareness
            + 0.27 * current_comm_strength
            + 0.12 * retention_memory
            + 0.10 * min(previous_share * max(self.B, 1), 1.0)
            + 0.05 * satisfaction_memory
        )

        effective_promo = float(np.clip(promo * self.promo_effect_mult, 0.0, 0.30))
        effective_dist = float(np.clip(dist * self.team_dist_mult[idx], 0.05, 1.0))

        brand_value_input = (
            0.60 * rrss
            + 0.30 * trad
            + 0.20 * pr
            + 1800.0 * max(0.0, 0.55 - quality)
            + 1200.0 * max(0.0, 8.2 - price)
            + 600.0 * product_perf
        ) * self.ad_effect_mult
        brand_premium_input = (
            1.00 * pr
            + 0.50 * trad
            + 0.30 * rrss
            + 0.10 * online
            + 1600.0 * product_design
            + 1800.0 * product_reliability
            + 1200.0 * product_perf
            - 1800.0 * max(effective_promo - 0.10, 0.0)
            - 900.0 * max(8.0 - price, 0.0)
        ) * self.ad_effect_mult
        projected_brand_value = max(self.brand_decay * float(self.brand_value[idx]) + brand_value_input, 0.0)
        projected_brand_premium = max(self.brand_decay * float(self.brand_premium[idx]) + brand_premium_input, 0.0)
        brand_value_term = np.log1p(projected_brand_value / 10000.0)
        brand_premium_term = np.log1p(projected_brand_premium / 10000.0)
        brand_consideration = clip01(0.55 * brand_value_term + 0.75 * brand_premium_term)
        positioning_strength = clip01(0.45 * brand_value_term + 0.70 * brand_premium_term)

        price_value_score = clip01((10.5 - price) / 4.5)
        price_consideration_score = clip01(1.0 - abs(price - 8.5) / 3.5)

        quality_supported_price = 7.7 + 4.6 * quality
        coherence = 0.0
        coherence -= 0.28 * max(price - quality_supported_price, 0.0)
        if brand_premium_term > brand_value_term + 0.03:
            coherence -= 1.10 * max(effective_promo - 0.12, 0.0)
            coherence -= 0.12 * max(8.0 - price, 0.0)
        coherence -= 0.22 * np.log1p(online / 7000.0) * (1.0 + 2.0 * max(0.58 - effective_dist, 0.0))
        coherence -= 0.16 * max(knowledge - effective_dist, 0.0)
        coherence += 0.12 * max(8.2 - price, 0.0) * min(effective_promo, 0.10)
        coherence += 0.12 * np.log1p((0.65 * pr + 0.35 * trad) / 7000.0) * max(quality - 0.58, 0.0)
        coherence -= 0.08 * max(0.50 - quality, 0.0)
        coherence = float(np.clip(coherence, -0.45, 0.35))
        coherence_strength = clip01(0.5 + coherence)

        consideration = clip01(
            0.22 * knowledge
            + 0.22 * quality
            + 0.20 * brand_consideration
            + 0.12 * price_consideration_score
            + 0.10 * effective_dist
            + 0.07 * satisfaction_memory
            + 0.07 * coherence_strength
        )

        projected_performance_stock = (
            self.perf_decay * float(self.performance_stock[idx])
            + (1.00 * online + 0.35 * rrss + 0.15 * trad + 0.05 * pr) * self.ad_effect_mult
        )
        performance_strength = log_strength(projected_performance_stock, scale=10000.0, divisor=1.35)
        promo_strength = clip01(effective_promo / 0.20)

        products_available = float(decision.get("products_available", decision.get("production_units", 0.0)))
        expected_units = float(decision.get("estimated_units_for_budget", max(previous_customers, 1.0)))
        if expected_units > 0 and products_available > 0:
            availability_strength = clip01(products_available / expected_units)
        else:
            availability_strength = 0.75

        purchase = clip01(
            0.26 * consideration
            + 0.20 * price_value_score
            + 0.18 * effective_dist
            + 0.15 * performance_strength
            + 0.11 * promo_strength
            + 0.06 * positioning_strength
            + 0.04 * availability_strength
        )

        promo_retention_effect = (
            0.10 * clip01(effective_promo / 0.08)
            if effective_promo <= 0.08
            else 0.10 * clip01(1.0 - (effective_promo - 0.08) / 0.22)
        )
        relationship_comm = log_strength(0.65 * pr + 0.35 * rrss, scale=10000.0, divisor=1.35)
        reliability_strength = clip01(0.55 * product_reliability + 0.45 * quality)

        retention = clip01(
            0.28 * satisfaction_memory
            + 0.22 * reliability_strength
            + 0.16 * quality
            + 0.12 * retention_memory
            + 0.08 * coherence_strength
            + 0.06 * relationship_comm
            + 0.05 * effective_dist
            + 0.03 * promo_retention_effect
        )

        return {
            "knowledge": float(knowledge * 100.0),
            "consideration": float(consideration * 100.0),
            "purchase": float(purchase * 100.0),
            "retention": float(retention * 100.0),
            "drivers": {
                "previous_awareness": float(previous_awareness * 100.0),
                "communication_strength": float(current_comm_strength * 100.0),
                "previous_share": float(previous_share * 100.0),
                "satisfaction_memory": float(satisfaction_memory * 100.0),
                "brand_consideration": float(brand_consideration * 100.0),
                "performance_strength": float(performance_strength * 100.0),
                "availability_strength": float(availability_strength * 100.0),
            },
        }

    # -----------------------------
    # STEP
    # -----------------------------
    def step(self, decisions):
        price = np.array([float(decisions[t]["price"]) for t in self.teams])
        promo = np.array([float(np.clip(decisions[t]["promo"], 0.0, 0.30)) for t in self.teams])
        dist = np.array([float(np.clip(decisions[t]["distribution"], 0.05, 1.0)) for t in self.teams])

        product_perf = np.array([
            float(np.clip(decisions[t].get("product_perf", 0.50), 0.0, 1.0))
            for t in self.teams
        ])
        product_design = np.array([
            float(np.clip(decisions[t].get("product_design", 0.50), 0.0, 1.0))
            for t in self.teams
        ])
        product_reliability = np.array([
            float(np.clip(decisions[t].get("product_reliability", 0.50), 0.0, 1.0))
            for t in self.teams
        ])

        # Índice agregado para costes, retención y reporting
        quality = (
            0.40 * product_perf +
            0.25 * product_design +
            0.35 * product_reliability
        )

        trad, online, rrss, pr = self._read_comm_channels(decisions)
        comm_total = trad + online + rrss + pr

        research_cost = np.array([
            float(decisions[t].get("research_cost", 0.0))
            for t in self.teams
        ])

        effective_promo = np.clip(promo * self.promo_effect_mult, 0.0, 0.30)
        effective_dist = np.clip(dist * self.team_dist_mult, 0.05, 1.0)

        # Más desarrollo de producto = más coste unitario
        quality_cost_mult = 1.0 + 0.20 * product_perf + 0.10 * product_design + 0.18 * product_reliability
        effective_unit_cost = (self.unit_cost * quality_cost_mult) * self.team_unit_cost_mult

        prev_units = self.customer_base.sum(axis=1)
        prev_total_units = prev_units.sum()
        if prev_total_units > 0:
            prev_share = prev_units / prev_total_units
        else:
            prev_share = np.full(self.B, 1.0 / self.B)

        # 1) CONOCIMIENTO DE MARCA
        # La notoriedad se apoya sobre todo en tradicional, RRSS, PR y cuota previa.
        # Online también suma, pero con menor peso porque se orienta más a compra.
        awareness_input = (
            0.28 * trad +
            0.24 * rrss +
            0.16 * pr +
            0.12 * online
        ) * self.ad_effect_mult

        self.aw_adstock = 0.72 * self.aw_adstock + awareness_input

        aw_comm_term = self.aw_adstock / max(self.aw_adstock.sum(), 1e-9)
        aw_share_term = prev_share

        self.awareness = np.clip(
            self.aw_decay * self.awareness
            + 0.14 * aw_comm_term
            + 0.10 * aw_share_term
            + self.team_awareness_boost,
            0.02,
            0.98
        )

        # 2) POSICIONAMIENTO DE MARCA
        brand_value_input = (
            0.60 * rrss +
            0.30 * trad +
            0.20 * pr
            + 1800.0 * np.maximum(0.0, 0.55 - quality)
            + 1200.0 * np.maximum(0.0, 8.2 - price)
            + 600.0 * product_perf
        ) * self.ad_effect_mult

        brand_premium_input = (
            1.00 * pr +
            0.50 * trad +
            0.30 * rrss +
            0.10 * online
            + 1600.0 * product_design
            + 1800.0 * product_reliability
            + 1200.0 * product_perf
            - 1800.0 * np.maximum(effective_promo - 0.10, 0.0)
            - 900.0 * np.maximum(8.0 - price, 0.0)
        ) * self.ad_effect_mult

        self.brand_value = np.maximum(
            self.brand_decay * self.brand_value + brand_value_input,
            0.0
        )
        self.brand_premium = np.maximum(
            self.brand_decay * self.brand_premium + brand_premium_input,
            0.0
        )

        # Online = ventas / compra
        performance_input = (
            1.00 * online +
            0.35 * rrss +
            0.15 * trad +
            0.05 * pr
        ) * self.ad_effect_mult

        self.performance_stock = self.perf_decay * self.performance_stock + performance_input

        mseg = self._market_size_by_segment()

        customers_by_team_seg = np.zeros((self.B, 3))
        retained_by_team_seg = np.zeros((self.B, 3))
        new_by_team_seg = np.zeros((self.B, 3))
        share_by_seg = np.zeros((self.B, 3))
        sales_power_by_seg = np.zeros((self.B, 3))
        retention_rate_by_team_seg = np.zeros((self.B, 3))

        prev_base = self.customer_base.copy()
        market_avg_price = float(np.mean(price))

        perf_term = np.log1p(self.performance_stock / 10_000)
        brand_value_term = np.log1p(self.brand_value / 10_000)
        brand_premium_term = np.log1p(self.brand_premium / 10_000)
        online_term_direct = np.log1p(online / 10_000)

        # Coherencia estratégica
        coherence_term, positioning_x, positioning_y = self._strategy_coherence(
            price=price,
            quality=quality,
            promo=effective_promo,
            effective_dist=effective_dist,
            online=online,
            trad=trad,
            rrss=rrss,
            pr=pr,
            brand_value_term=brand_value_term,
            brand_premium_term=brand_premium_term,
            awareness_level=self.awareness
        )

        brand_consideration_term = (
            0.55 * brand_value_term +
            0.75 * brand_premium_term
        )

        # 3) CONSIDERACIÓN
        # Producto, posicionamiento, precio y distribución explican gran parte del
        # interés real por la marca antes de la compra.
        fair_price_term = np.clip(1.12 - np.log(price), 0.0, 1.0)
        consideration = np.clip(
            0.06
            + 0.20 * self.awareness
            + 0.08 * np.log(effective_dist)
            + 0.07 * online_term_direct
            + 0.10 * np.log1p((0.60 * rrss + 0.40 * pr + 0.25 * trad) / 10_000)
            + 0.12 * product_perf
            + 0.12 * product_design
            + 0.14 * product_reliability
            + 0.18 * brand_consideration_term
            + 0.08 * fair_price_term
            + 0.05 * np.clip(self.satisfaction, -0.6, 1.5)
            + 0.10 * coherence_term
            + self.rng.normal(0.0, 0.02, size=self.B),
            0.02,
            0.98
        )

        # Lectura pedagógica del funnel: qué tan bien está trabajada cada fase.
        knowledge_stage = np.clip(
            0.28 * (trad / max(comm_total.max(), 1.0))
            + 0.24 * (rrss / max(comm_total.max(), 1.0))
            + 0.16 * (pr / max(comm_total.max(), 1.0))
            + 0.12 * (online / max(comm_total.max(), 1.0))
            + 0.20 * prev_share,
            0.0,
            1.0
        )

        consideration_stage = np.clip(
            0.26 * quality
            + 0.24 * np.clip(0.55 * brand_value_term + 0.85 * brand_premium_term, 0.0, 1.0)
            + 0.14 * fair_price_term
            + 0.10 * effective_dist
            + 0.10 * np.clip(rrss / max(comm_total.max(), 1.0), 0.0, 1.0)
            + 0.08 * np.clip(online / max(comm_total.max(), 1.0), 0.0, 1.0)
            + 0.08 * np.clip(trad / max(comm_total.max(), 1.0), 0.0, 1.0),
            0.0,
            1.0
        )

        purchase_stage = np.clip(
            0.25 * fair_price_term
            + 0.24 * effective_promo
            + 0.22 * effective_dist
            + 0.16 * np.clip(online / max(comm_total.max(), 1.0), 0.0, 1.0)
            + 0.13 * np.clip(0.45 * brand_value_term + 0.70 * brand_premium_term, 0.0, 1.0),
            0.0,
            1.0
        )

        retention_stage = np.clip(
            0.30 * np.clip(0.5 + 0.5 * np.clip(self.satisfaction, -0.6, 1.5) / 1.5, 0.0, 1.0)
            + 0.24 * quality
            + 0.16 * np.clip(0.5 + coherence_term, 0.0, 1.0)
            + 0.10 * np.clip(0.08 + np.minimum(effective_promo, 0.08) - 1.8 * np.maximum(effective_promo - 0.10, 0.0), 0.0, 1.0)
            + 0.08 * np.clip(pr / max(comm_total.max(), 1.0), 0.0, 1.0)
            + 0.06 * np.clip(rrss / max(comm_total.max(), 1.0), 0.0, 1.0)
            + 0.06 * effective_dist,
            0.0,
            1.0
        )

        # 4) ACTIVACIÓN DINÁMICA DE SEGMENTOS
        # Antes, cada segmento tenía un porcentaje fijo de consumidores activos:
        # Ahorradores 41%, Equilibrados 46%, Exigentes 51%.
        # Ahora ese porcentaje depende de la presión de comunicación agregada del mercado,
        # del encaje de canales por segmento, del precio medio y de la saturación publicitaria.
        channel_weights_by_segment = np.array([
            [0.35, 0.30, 0.25, 0.10],  # Ahorradores: tradicional/online y RRSS activan más.
            [0.25, 0.25, 0.30, 0.20],  # Equilibrados: respuesta más balanceada.
            [0.20, 0.15, 0.25, 0.40],  # Exigentes: mayor sensibilidad a RR.PP. y marca.
        ])
        base_activation_rate = np.array([0.41, 0.46, 0.51])
        activation_sensitivity = np.array([0.08, 0.10, 0.12])

        market_channel_pressure = np.array([
            float(trad.sum()),
            float(online.sum()),
            float(rrss.sum()),
            float(pr.sum()),
        ]) * self.ad_effect_mult

        segment_comm_pressure = channel_weights_by_segment @ market_channel_pressure
        segment_activation_boost = activation_sensitivity * np.log1p(segment_comm_pressure / 30000.0)

        avg_market_price = float(np.mean(price))
        activation_price_penalty = np.clip((avg_market_price - 8.5) * 0.025, 0.0, 0.08)
        activation_saturation_penalty = np.clip((float(comm_total.sum()) - 140000.0) / 900000.0, 0.0, 0.08)

        segment_activation_rate = np.clip(
            base_activation_rate
            + segment_activation_boost
            - activation_price_penalty
            - activation_saturation_penalty,
            0.25,
            0.75
        )
        segment_non_buyers_rate = 1.0 - segment_activation_rate

        for s in range(3):
            cheap_penalty = 0.10 * np.maximum(8.0 - price, 0.0)

            if s == 0:  # Ahorradores
                brand_effect = 1.15 * brand_value_term + 0.25 * brand_premium_term
                promo_effect = 1.35 * effective_promo
                product_fit = (
                    0.18 * product_perf +
                    0.03 * product_design +
                    0.09 * product_reliability
                )
                consideration_price_effect = 0.18 * fair_price_term
                purchase_positioning_effect = 0.08 * brand_value_term + 0.03 * brand_premium_term
            elif s == 1:  # Equilibrados
                brand_effect = 0.70 * brand_value_term + 0.70 * brand_premium_term
                promo_effect = 1.00 * effective_promo
                product_fit = (
                    0.11 * product_perf +
                    0.10 * product_design +
                    0.12 * product_reliability
                )
                consideration_price_effect = 0.12 * fair_price_term
                purchase_positioning_effect = 0.06 * brand_value_term + 0.06 * brand_premium_term
            else:  # Exigentes
                brand_effect = 0.25 * brand_value_term + 1.25 * brand_premium_term
                promo_effect = 0.45 * effective_promo
                product_fit = (
                    0.06 * product_perf +
                    0.16 * product_design +
                    0.14 * product_reliability
                )
                consideration_price_effect = 0.05 * fair_price_term
                purchase_positioning_effect = 0.03 * brand_value_term + 0.10 * brand_premium_term

            perceived_product_level = (
                self.product_weights[s, 0] * product_perf +
                self.product_weights[s, 1] * product_design +
                self.product_weights[s, 2] * product_reliability
            )

            quality_price_mismatch = np.maximum(price - (7.8 + 4.5 * perceived_product_level), 0.0)

            U = (
                self.base_pref[:, s]
                + 0.30 * self.awareness
                + 0.22 * np.log(effective_dist)
                + consideration_price_effect
                + 0.08 * np.log1p((0.65 * rrss + 0.35 * pr) / 10_000)
                + 0.06 * np.log1p((0.55 * online + 0.25 * trad) / 10_000)
                + brand_effect
                + 0.10 * np.clip(self.satisfaction, -0.6, 1.5)
                + product_fit
                + 0.20 * coherence_term
                - 0.12 * quality_price_mismatch
                + (self.b_price[s] * self.price_sens_mult) * np.log(price)
                + self.rng.normal(0.0, 0.04, size=self.B)
            )

            share = softmax(U)
            share_by_seg[:, s] = share

            sales_power = (
                0.45 * consideration
                + 0.18 * promo_effect
                + 0.18 * np.log(effective_dist)
                + 0.15 * perf_term
                + 0.10 * online_term_direct
                + purchase_positioning_effect
                + 0.08 * coherence_term
                + 0.05 * np.clip(self.satisfaction, -0.6, 1.5)
                - 0.06 * quality_price_mismatch
                - 0.04 * np.maximum(price - market_avg_price, 0.0)
            )
            sales_power = np.clip(sales_power, 0.02, 0.72)
            sales_power_by_seg[:, s] = sales_power

            seg_customers_total = mseg[s] * segment_activation_rate[s]

            promo_bonus = 0.04 * np.minimum(effective_promo, 0.08)
            promo_penalty = 0.36 * np.maximum(effective_promo - 0.10, 0.0)
            promo_loyalty_penalty = 0.08 * effective_promo

            if s == 0:
                retention_product_effect = (
                    0.09 * product_perf +
                    0.03 * product_design +
                    0.12 * product_reliability
                )
            elif s == 1:
                retention_product_effect = (
                    0.08 * product_perf +
                    0.07 * product_design +
                    0.13 * product_reliability
                )
            else:
                retention_product_effect = (
                    0.06 * product_perf +
                    0.11 * product_design +
                    0.15 * product_reliability
                )

            retention = (
                self.base_retention[s]
                + 0.18 * np.clip(self.satisfaction, -0.6, 1.5)
                + retention_product_effect
                + 0.07 * coherence_term
                + 0.05 * np.log(effective_dist)
                + 0.04 * np.log1p((0.65 * pr + 0.35 * rrss) / 10_000)
                + 0.06 * self.awareness
                + 0.08 * brand_premium_term
                + 0.05 * brand_value_term
                + promo_bonus
                - promo_penalty
                - promo_loyalty_penalty
                - 0.08 * np.maximum(price - 8.0, 0.0)
                - 0.04 * np.maximum(price - market_avg_price, 0.0)
                - 0.10 * quality_price_mismatch
                + self.rng.normal(0.0, 0.018, size=self.B)
            )
            retention = np.clip(retention, 0.18, 0.93)
            retention_rate_by_team_seg[:, s] = retention

            retained = prev_base[:, s] * retention
            retained_by_team_seg[:, s] = retained

            attractiveness = consideration * share * sales_power
            attractiveness_sum = attractiveness.sum()

            free_pool = max(seg_customers_total - retained.sum(), 0.0)

            if attractiveness_sum > 0:
                new_customers = free_pool * (attractiveness / attractiveness_sum)
            else:
                new_customers = np.full(self.B, free_pool / self.B)

            new_by_team_seg[:, s] = new_customers
            customers_by_team_seg[:, s] = retained + new_customers

        customers_by_team_seg *= self.team_capacity_mult[:, None]
        retained_by_team_seg *= self.team_capacity_mult[:, None]
        new_by_team_seg *= self.team_capacity_mult[:, None]

        # Demanda potencial antes de limitar por productos disponibles.
        demand_potential = customers_by_team_seg.sum(axis=1)

        production_units = np.array([
            float(decisions[t].get("production_units", max(demand_potential[i] * 1.05, 0.0)))
            for i, t in enumerate(self.teams)
        ])
        production_units = np.maximum(production_units, 0.0)
        inventory_start = self.inventory.copy()
        products_available = production_units + inventory_start

        fulfilment_rate = np.divide(
            np.minimum(demand_potential, products_available),
            demand_potential,
            out=np.ones_like(demand_potential),
            where=demand_potential > 0
        )
        fulfilment_rate = np.clip(fulfilment_rate, 0.0, 1.0)

        customers_by_team_seg *= fulfilment_rate[:, None]
        retained_by_team_seg *= fulfilment_rate[:, None]
        new_by_team_seg *= fulfilment_rate[:, None]

        units = customers_by_team_seg.sum(axis=1)
        inventory_final = np.maximum(products_available - units, 0.0)
        stockout_units = np.maximum(demand_potential - products_available, 0.0)
        self.inventory = inventory_final.copy()

        retained_customers = retained_by_team_seg.sum(axis=1)
        new_customers = new_by_team_seg.sum(axis=1)
        lost_customers = np.maximum(prev_base.sum(axis=1) - retained_by_team_seg.sum(axis=1), 0.0)

        total_units = units.sum()
        share_total = units / total_units if total_units > 0 else np.full(self.B, 1.0 / self.B)

        retained_pct = np.divide(
            retained_customers,
            units,
            out=np.zeros_like(retained_customers),
            where=units > 0
        )

        new_pct = np.divide(
            new_customers,
            units,
            out=np.zeros_like(new_customers),
            where=units > 0
        )

        retention_rate_total = np.divide(
            retained_customers,
            prev_base.sum(axis=1),
            out=np.zeros_like(retained_customers),
            where=prev_base.sum(axis=1) > 0
        )

        value_score = (
            0.30 * retention_rate_total
            + 0.20 * quality
            + 0.16 * np.clip(0.5 + coherence_term, 0.0, 1.0)
            + 0.10 * np.log(effective_dist)
            + 0.10 * brand_premium_term
            + 0.08 * brand_value_term
            + 0.06 * np.log1p((0.60 * pr + 0.40 * rrss) / 10_000)
            + 0.05 * self.awareness
            - 0.10 * np.maximum(effective_promo - 0.15, 0.0)
            - 0.08 * np.maximum(price - 8.8, 0.0)
        )

        self.satisfaction = np.clip(
            0.72 * self.satisfaction + 0.28 * value_score,
            -0.6,
            1.5
        )

        # COSTES Y BENEFICIO
        promo_cost = (promo * price) * units * 0.55
        dist_cost = 1500 * effective_dist + 2500 * (effective_dist ** 2)
        production_cost = effective_unit_cost * production_units

        # Inversión de producto
        product_investment_cost = (
            12000 * product_perf +
            9000 * product_design +
            14000 * product_reliability
        )

        revenue = price * units
        gross_margin = (price - effective_unit_cost) * units

        # Coste de almacenamiento del inventario sobrante.
        # No consume presupuesto de marketing, pero reduce el beneficio empresarial.
        storage_cost = self.STORAGE_COST_RATE * effective_unit_cost * inventory_final

        profit_before_storage = gross_margin - comm_total - promo_cost - dist_cost - product_investment_cost - research_cost
        profit = profit_before_storage - storage_cost

        budget_available = np.array([
            float(decisions[t].get("budget_available", 0.0))
            for t in self.teams
        ])
        budget_used_actual = comm_total + promo_cost + dist_cost + product_investment_cost + research_cost
        budget_remaining_actual = budget_available - budget_used_actual

        truth = []
        for i, t in enumerate(self.teams):
            truth.append({
                "team": t,
                "units": float(units[i]),
                "demand_potential": float(demand_potential[i]),
                "production_units": float(production_units[i]),
                "inventory_start": float(inventory_start[i]),
                "products_available": float(products_available[i]),
                "inventory_final": float(inventory_final[i]),
                "stockout_units": float(stockout_units[i]),
                "fulfilment_rate": float(fulfilment_rate[i]),
                "share": float(share_total[i]),
                "revenue": float(revenue[i]),
                "profit_before_storage": float(profit_before_storage[i]),
                "storage_cost": float(storage_cost[i]),
                "storage_cost_rate": float(self.STORAGE_COST_RATE),
                "profit": float(profit[i]),
                "awareness_true": float(self.awareness[i]),
                "price": float(price[i]),
                "promo": float(promo[i]),
                "distribution": float(dist[i]),

                "product_perf": float(product_perf[i]),
                "product_design": float(product_design[i]),
                "product_reliability": float(product_reliability[i]),
                "quality": float(quality[i]),

                "comm_trad": float(trad[i]),
                "comm_online": float(online[i]),
                "comm_rrss": float(rrss[i]),
                "comm_pr": float(pr[i]),
                "comm_total": float(comm_total[i]),

                "research_cost": float(research_cost[i]),

                "promo_cost": float(promo_cost[i]),
                "dist_cost": float(dist_cost[i]),
                "product_investment_cost": float(product_investment_cost[i]),

                "unit_cost_base": float(self.unit_cost[i]),
                "unit_cost_final": float(effective_unit_cost[i]),
                "production_cost": float(production_cost[i]),

                "budget_available": float(budget_available[i]),
                "budget_used_actual": float(budget_used_actual[i]),
                "budget_remaining_actual": float(budget_remaining_actual[i]),

                "retained_customers": float(retained_customers[i]),
                "new_customers": float(new_customers[i]),
                "lost_customers": float(lost_customers[i]),
                "retained_pct": float(retained_pct[i]),
                "new_pct": float(new_pct[i]),
                "retention_rate": float(retention_rate_total[i]),
                "satisfaction": float(self.satisfaction[i]),

                "brand_value": float(brand_value_term[i]),
                "brand_premium": float(brand_premium_term[i]),

                "strategy_coherence": float(coherence_term[i]),
                "positioning_value_price": float(positioning_x[i]),
                "positioning_quality": float(positioning_y[i]),
                "funnel_knowledge": float(knowledge_stage[i]),
                "funnel_consideration": float(consideration_stage[i]),
                "funnel_purchase": float(purchase_stage[i]),
                "funnel_retention": float(retention_stage[i]),
            })

        sample_n = 1500

        def noisy(p, extra_sd):
            p = float(np.clip(p, 0.0001, 0.9999))
            se = np.sqrt(p * (1 - p) / sample_n)
            est = p + self.rng.normal(0.0, se + extra_sd)
            return float(np.clip(est, 0.0, 1.0))

        segment_brand_mix = {}
        for s, seg_name in enumerate(self.seg_names):
            segment_brand_mix[seg_name] = {
                self.teams[i]: float(share_by_seg[i, s])
                for i in range(self.B)
            }

        segment_sizes = {
            self.seg_names[s]: float(mseg[s])
            for s in range(len(self.seg_names))
        }

        segment_activation_rate_report = {
            self.seg_names[s]: float(segment_activation_rate[s])
            for s in range(len(self.seg_names))
        }
        segment_non_buyers_rate_report = {
            self.seg_names[s]: float(segment_non_buyers_rate[s])
            for s in range(len(self.seg_names))
        }
        segment_active_buyers_report = {
            self.seg_names[s]: float(mseg[s] * segment_activation_rate[s])
            for s in range(len(self.seg_names))
        }
        segment_non_buyers_report = {
            self.seg_names[s]: float(mseg[s] * segment_non_buyers_rate[s])
            for s in range(len(self.seg_names))
        }
        segment_comm_pressure_report = {
            self.seg_names[s]: float(segment_comm_pressure[s])
            for s in range(len(self.seg_names))
        }

        estimated_comm_effects = {}
        for i, t in enumerate(self.teams):
            knowledge_score = float(np.clip(np.log1p(awareness_input[i] / 10_000) / 1.2, 0.0, 1.0))
            estimated_comm_effects[t] = {
                "performance": float(np.clip(np.log1p(performance_input[i] / 10_000) / 1.2, 0.0, 1.0)),
                "knowledge": knowledge_score,
                "awareness": knowledge_score,  # alias para compatibilidad
                "brand_value": float(np.clip(np.log1p(max(brand_value_input[i], 0.0) / 10_000) / 1.2, 0.0, 1.0)),
                "brand_premium": float(np.clip(np.log1p(max(brand_premium_input[i], 0.0) / 10_000) / 1.2, 0.0, 1.0)),
            }

        estimated_knowledge = {t["team"]: noisy(t["awareness_true"], 0.015) for t in truth}

        research = {
            "sample_n": sample_n,
            "estimated_share": {t["team"]: noisy(t["share"], 0.012) for t in truth},
            "estimated_knowledge": estimated_knowledge,
            "estimated_awareness": estimated_knowledge,  # alias para compatibilidad
            "estimated_retained_pct": {t["team"]: noisy(t["retained_pct"], 0.025) for t in truth},
            "estimated_new_pct": {t["team"]: noisy(t["new_pct"], 0.025) for t in truth},
            "observed_avg_price": {t["team"]: float(t["price"] + self.rng.normal(0.0, 0.05)) for t in truth},
            "estimated_quality": {
                t["team"]: float(np.clip(t["quality"] + self.rng.normal(0.0, 0.04), 0.0, 1.0))
                for t in truth
            },
            "estimated_product_perf": {
                t["team"]: float(np.clip(t["product_perf"] + self.rng.normal(0.0, 0.05), 0.0, 1.0))
                for t in truth
            },
            "estimated_product_design": {
                t["team"]: float(np.clip(t["product_design"] + self.rng.normal(0.0, 0.05), 0.0, 1.0))
                for t in truth
            },
            "estimated_product_reliability": {
                t["team"]: float(np.clip(t["product_reliability"] + self.rng.normal(0.0, 0.05), 0.0, 1.0))
                for t in truth
            },
            "estimated_brand_value": {
                t["team"]: noisy(np.clip(t["brand_value"] / 1.0, 0.0, 0.999), 0.03)
                for t in truth
            },
            "estimated_brand_premium": {
                t["team"]: noisy(np.clip(t["brand_premium"] / 1.0, 0.0, 0.999), 0.03)
                for t in truth
            },
            "estimated_strategy_coherence": {
                t["team"]: float(np.clip(0.5 + t["strategy_coherence"], 0.0, 1.0))
                for t in truth
            },
            "estimated_positioning_value_price": {
                t["team"]: float(np.clip(t["positioning_value_price"] + self.rng.normal(0.0, 0.04), 0.0, 1.0))
                for t in truth
            },
            "estimated_positioning_quality": {
                t["team"]: float(np.clip(t["positioning_quality"] + self.rng.normal(0.0, 0.04), 0.0, 1.0))
                for t in truth
            },
            "estimated_funnel_knowledge": {
                t["team"]: float(np.clip(t["funnel_knowledge"] + self.rng.normal(0.0, 0.03), 0.0, 1.0))
                for t in truth
            },
            "estimated_funnel_consideration": {
                t["team"]: float(np.clip(t["funnel_consideration"] + self.rng.normal(0.0, 0.03), 0.0, 1.0))
                for t in truth
            },
            "estimated_funnel_purchase": {
                t["team"]: float(np.clip(t["funnel_purchase"] + self.rng.normal(0.0, 0.03), 0.0, 1.0))
                for t in truth
            },
            "estimated_funnel_retention": {
                t["team"]: float(np.clip(t["funnel_retention"] + self.rng.normal(0.0, 0.03), 0.0, 1.0))
                for t in truth
            },
            "segment_brand_mix": segment_brand_mix,
            "segment_sizes": segment_sizes,
            "segment_activation_rate": segment_activation_rate_report,
            "segment_non_buyers_rate": segment_non_buyers_rate_report,
            "segment_active_buyers": segment_active_buyers_report,
            "segment_non_buyers": segment_non_buyers_report,
            "segment_comm_pressure": segment_comm_pressure_report,
            "estimated_comm_effects": estimated_comm_effects,
            "notes": "Estimaciones con error muestral y ruido (no son la verdad)."
        }

        diagnostics = {
            "customers_by_team_segment": customers_by_team_seg,
            "retained_by_team_segment": retained_by_team_seg,
            "new_by_team_segment": new_by_team_seg,
            "share_by_segment": share_by_seg,
            "sales_power_by_team_segment": sales_power_by_seg,
            "retention_rate_by_team_segment": retention_rate_by_team_seg,
            "market_size_by_segment": mseg,
            "segment_activation_rate": segment_activation_rate.copy(),
            "segment_non_buyers_rate": segment_non_buyers_rate.copy(),
            "segment_active_buyers": mseg * segment_activation_rate,
            "segment_non_buyers": mseg * segment_non_buyers_rate,
            "segment_comm_pressure": segment_comm_pressure.copy(),
            "activation_price_penalty": float(activation_price_penalty),
            "activation_saturation_penalty": float(activation_saturation_penalty),
            "awareness_input": awareness_input,
            "brand_value_input": brand_value_input,
            "brand_premium_input": brand_premium_input,
            "performance_input": performance_input,
            "consideration": consideration,
            "satisfaction": self.satisfaction.copy(),
            "storage_cost": storage_cost.copy(),
            "profit_before_storage": profit_before_storage.copy(),
            "product_perf": product_perf.copy(),
            "product_design": product_design.copy(),
            "product_reliability": product_reliability.copy(),
            "quality": quality.copy(),
            "strategy_coherence": coherence_term.copy(),
            "positioning_value_price": positioning_x.copy(),
            "positioning_quality": positioning_y.copy(),
            "funnel_knowledge": knowledge_stage.copy(),
            "funnel_consideration": consideration_stage.copy(),
            "funnel_purchase": purchase_stage.copy(),
            "funnel_retention": retention_stage.copy(),
        }

        self.customer_base = customers_by_team_seg.copy()

        self.t += 1
        self._reset_round_modifiers()
        return truth, research, diagnostics