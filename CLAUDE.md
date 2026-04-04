# CLAUDE.md — Hackea tu Metabolismo con IA
## Subagente v1.3 — S1-S14 completos · Auth Supabase · i18n ES/EN

---

## ROL DEL AGENTE

Eres el motor científico de **Hackea tu Metabolismo con IA** — un programa
personalizado de pérdida de peso basado en ciencia real, sin dietas, sin humo.

Tienes formación y experiencia activa en:

**Ciencias de la salud:** Ingeniero metabólico, nutriólogo clínico, nutricionista
con enfoque en metabolismo humano, composición corporal, crononutrición y
nutrición basada en evidencia. Dominas rutas metabólicas (glucólisis, ciclo de
Krebs, β-oxidación), sarcopenia, resistencia insulínica y cambios hormonales por edad.

**Análisis de datos:** Python (pandas, numpy, scikit-learn, statsmodels, plotly),
estadística inferencial, modelos predictivos, clustering.

**BI y datos:** SQL/SQLite/PostgreSQL, Streamlit, Power BI.

**Principio rector:** Sin humo. Sin dietas milagro. Solo termodinámica,
hábitos reales y consistencia. Cada recomendación tiene respaldo científico.

---

## IDENTIDAD DEL PRODUCTO

| Campo | Valor |
|---|---|
| Nombre | Hackea tu Metabolismo con IA |
| Tagline | Ciencia real · Sin humo · Sin dietas · Con resultados |
| Powered by | Claude (Anthropic) + Open Food Facts + USDA |
| Idioma | Bilingüe ES/EN (selector en UI) |
| Plataforma | Web responsive (Streamlit, port 8505) |
| Tema visual | Dark navy (#0a1628) + Teal (#0f9d7a) + Coral (#e55c2f) + Violeta (#7f77dd) |

---

## STACK TECNOLÓGICO

| Capa | Tecnología |
|---|---|
| Frontend | Streamlit responsive |
| IA / Visión | Anthropic API (Claude Sonnet) |
| Nutrición DB | Open Food Facts API + USDA FoodData Central |
| DB dev | SQLite (`data/hackea_metabolismo.db`) |
| DB prod | Supabase (PostgreSQL + Auth + Storage) |
| Auth | Supabase Auth |
| Fotos | Supabase Storage |
| Deploy | Streamlit Community Cloud |

---

## ESTRUCTURA DEL PROYECTO

```
C:\ClaudeWork\HackeaMetabolismo\
│
├── CLAUDE.md                    ← este archivo
├── PRD.md                       ← Product Requirements Document
├── CLAUDE_PATCH_40plus.md       ← protocolo científico +40 años
├── README.md
├── .env
├── requirements.txt
│
├── data/
│   ├── hackea_metabolismo.db    ← SQLite dev
│   ├── ejercicios.json          ← catálogo de rutinas
│   └── alimentos_latam.csv      ← alimentos locales LATAM
│
├── src/
│   ├── core/
│   │   ├── calculos.py          ← TMB, TDEE, macros, déficit, TEF
│   │   ├── calculos_40plus.py   ← sarcopenia, WHtR, hormonas, crononutrición
│   │   ├── plateau.py           ← detección meseta, refeed, diet break
│   │   └── progreso.py          ← tendencias, proyecciones, media móvil
│   ├── alimentacion/
│   │   ├── openfoodfacts.py     ← búsqueda por texto y barcode
│   │   ├── vision_ia.py         ← foto → Claude Vision → JSON estimación
│   │   └── recetas_ia.py        ← ingredientes → recetas → lista compras
│   ├── ejercicio/
│   │   └── rutinas.py           ← catálogo, progresión, jerarquía +40
│   ├── db/
│   │   ├── schema.py            ← CREATE TABLE SQLite
│   │   ├── queries.py           ← CRUD operations
│   │   └── supabase_client.py   ← cliente Supabase (prod)
│   └── utils/
│       ├── i18n.py              ← traducciones ES/EN (~200 claves)
│       ├── auth_guard.py        ← require_auth(), auth_badge()
│       └── helpers.py
│
├── dashboard/
│   ├── app.py                   ← entrada principal (port 8505)
│   └── pages/
│       ├── 00_Login.py          ← auth Supabase: login/registro/recuperar
│       ├── 01_Onboarding.py     ← perfil + protocolo +40
│       ├── 02_Dashboard.py      ← anillo kcal, macros, alertas
│       ├── 03_Registro.py       ← foto IA + texto + barcode
│       ├── 04_Ejercicio.py      ← rutinas + log + ajuste TDEE
│       ├── 05_Progreso.py       ← peso, medidas, fotos, gráficos
│       ├── 06_Planificacion.py  ← recetas IA + lista compras
│       ├── 07_Sueno.py          ← sueño/cortisol (protocolo +40)
│       └── 08_Meseta.py         ← plateau, refeed, diet break
│
├── tests/
│   └── test_calculos.py
│
└── launchers/
    ├── setup.bat
    └── run.bat
```

---

## REGLAS DE NEGOCIO CRÍTICAS (hard limits — nunca violar)

```python
# ── Calorías mínimas ──────────────────────────────────────────
KCAL_MIN_FEMENINO   = 1200
KCAL_MIN_MASCULINO  = 1500
DEFICIT_MAX_KCAL    = 750     # si usuario pide más → advertencia con evidencia

# ── Objetivo de pérdida ───────────────────────────────────────
META_SEMANAL_KG     = 0.5     # –0.5 kg/semana = estándar científico
DEFICIT_TARGET      = (300, 500)  # rango kcal/día

# ── Meseta (plateau) ──────────────────────────────────────────
PLATEAU_SEMANAS         = 3    # semanas sin progreso
PLATEAU_ADHERENCIA_MIN  = 0.80 # % adherencia mínima para confirmar plateau

# ── TDEE dinámico ─────────────────────────────────────────────
TDEE_RECALCULO_DIAS = 14       # recalcular cada 14 días con peso real

# ── Protocolo +40 ─────────────────────────────────────────────
EDAD_PROTOCOLO_40PLUS    = 40
PROTEINA_MIN_G_KG_40PLUS = 2.0   # vs 1.6 para <40
FACTOR_CORRECTOR_40_49   = 0.97
FACTOR_CORRECTOR_50_59   = 0.95
FACTOR_CORRECTOR_60_MAS  = 0.92
WHtR_RIESGO_ALTO         = 0.60
HORA_ULTIMA_COMIDA_ALERTA = 20   # alertar si última comida > 20h
SUENO_HORAS_MINIMO       = 7.0
```

---

## FÓRMULAS CORE

```python
# ── TMB (Mifflin-St Jeor) ─────────────────────────────────────
def calcular_tmb(peso_kg, talla_cm, edad, sexo):
    base = 10 * peso_kg + 6.25 * talla_cm - 5 * edad
    return base + (5 if sexo == 'M' else -161)

# ── TDEE con factor edad ──────────────────────────────────────
FACTORES_ACTIVIDAD = {
    'sedentario': 1.2, 'ligero': 1.375, 'moderado': 1.55,
    'activo': 1.725, 'muy_activo': 1.9
}
FACTORES_EDAD = {(40,49): 0.97, (50,59): 0.95, (60,99): 0.92}

def calcular_tdee(tmb, nivel_actividad, edad):
    tdee = tmb * FACTORES_ACTIVIDAD[nivel_actividad]
    for (min_e, max_e), factor in FACTORES_EDAD.items():
        if min_e <= edad <= max_e:
            tdee *= factor
    return round(tdee, 0)

# ── Macros en déficit ─────────────────────────────────────────
def calcular_macros(peso_kg, kcal_objetivo, edad):
    p_min = 2.0 if edad >= 40 else 1.6
    proteina_g     = peso_kg * p_min
    grasa_g        = (kcal_objetivo * 0.30) / 9
    carbohidrato_g = (kcal_objetivo - proteina_g*4 - grasa_g*9) / 4
    return proteina_g, carbohidrato_g, grasa_g

# ── TEF (Efecto Térmico de los Alimentos) ────────────────────
def calcular_tef(proteina_g, carbohidrato_g, grasa_g):
    return (proteina_g*4*0.27 + carbohidrato_g*4*0.07 + grasa_g*9*0.03)

# ── WHtR (Índice cintura/estatura) ────────────────────────────
def calcular_whtr(cintura_cm, talla_cm):
    return round(cintura_cm / talla_cm, 3)
    # Meta universal: < 0.50
```

---

## JERARQUÍA DE EJERCICIO EN +40 (obligatoria)

1. **FUERZA** (≥2 sesiones/semana) — preserva músculo, mejora insulino-sensibilidad
2. **CARDIO MODERADO** (150 min/semana) — caminata rápida, bici, natación
3. **HIIT** (1–2 sesiones/semana, 20 min) — más efectivo que steady-state
4. **MOVILIDAD** (10–15 min/día) — prevención lesiones, reducción cortisol

⚠️ NUNCA: déficit agresivo + cardio de alto volumen sin fuerza en +40

---

## MÓDULO IA — REGISTRO POR FOTO (flujo)

```
1. Usuario sube foto del plato
2. Claude Vision recibe imagen + prompt estructurado en JSON
3. Respuesta: {alimentos:[], porciones_g:[], kcal_min:int, kcal_max:int, macros:{}}
4. App muestra estimación con rango de incertidumbre al usuario
5. Usuario confirma o ajusta
6. Se guarda con flag es_estimado=True y campo confianza_ia
```

Prompt Claude Vision (usar siempre — ver `src/alimentacion/vision_ia.py:PROMPT_VISION`):
```
Analiza esta imagen de comida o producto alimenticio. Estima con precisión los valores
nutricionales REALES según el tipo de alimento visible.

REGLAS IMPORTANTES:
1. Si ves un producto ENVASADO (chocolate, galletas, snack, bebida): usa valores típicos
   por 100g de ese producto específico. Ejemplo: chocolate blanco ~550 kcal/100g,
   8g proteína, 57g carbs, 33g grasa.
2. Si ves un PLATO COCINADO: estima la porción visible en gramos y calcula los macros.
3. Los macros DEBEN ser coherentes: kcal ≈ proteína×4 + carbohidratos×4 + grasa×9 (±10%).
4. NUNCA copies valores de ejemplo. Estima según el alimento real.

Responde SOLO en JSON:
{
  "alimentos": ["nombre real del alimento o producto"],
  "porciones_g": [gramos estimados de la porción visible],
  "kcal_estimadas_min": <entero>,
  "kcal_estimadas_max": <entero>,
  "proteina_g": <gramos reales de proteína para la porción>,
  "carbohidrato_g": <gramos reales de carbohidratos para la porción>,
  "grasa_g": <gramos reales de grasa para la porción>,
  "confianza": "alta|media|baja",
  "notas": "tipo de alimento detectado y base de estimación"
}
```

⚠️ NUNCA poner valores numéricos fijos en el template — el AI los copia literalmente (bug conocido).
Post-procesamiento: `_validar_coherencia()` recalcula kcal si divergen >25% de los macros.

---

## ALERTAS DEL SISTEMA

```python
ALERTAS = [
    # Meseta
    ("plateau_detectado",    "danger",  "Meseta detectada: 3 semanas sin progreso. Sugiero refeed day."),
    # Déficit agresivo
    ("deficit_muy_agresivo", "warning", "Déficit > 750 kcal puede causar pérdida muscular. Ajustando."),
    # Timing comidas (+40)
    ("comida_tarde_40plus",  "warning", "Última comida > 20h en +40 favorece grasa visceral."),
    # Sueño
    ("sueno_insuficiente",   "warning", "< 7h de sueño eleva cortisol y dificulta pérdida de grasa."),
    # Fuerza ausente
    ("sin_fuerza_40plus",    "danger",  "Sin fuerza esta semana: riesgo de pérdida muscular en déficit."),
    # WHtR
    ("whtr_alto",            "danger",  "Índice cintura/estatura ≥ 0.60: prioridad grasa visceral."),
    # Proteína baja
    ("proteina_baja",        "info",    "Proteína < 80% objetivo: músculo en riesgo en déficit."),
    # Calorías líquidas
    ("calorias_liquidas",    "info",    "Bebidas calóricas > 10% kcal diarias. Impacto en insulina."),
]
```

---

## CONVENCIONES DE CÓDIGO

- **Python command:** `py` / `py -m pip`
- **Encoding:** UTF-8 en todos los archivos
- **Comentar, no borrar:** código desactivado → `# [DISABLED]`
- **Env vars:** siempre desde `.env` vía `python-dotenv`
- **Logging:** `logging` estándar, no `print()` en producción
- **Estimaciones IA:** siempre mostrar rango (ej: "310–340 kcal"), nunca un valor único
- **Port:** 8505 (no colisionar con finanzas_personales:8503, NutriMetab:8504)

---

## SPRINTS

| Sprint | Módulo | Entregable | Estado |
|---|---|---|---|
| S1 | Infra + DB | Schema SQLite, estructura carpetas, .env | ✅ |
| S2 | Onboarding | Perfil, TMB/TDEE, macros, flag +40, WHtR | ✅ |
| S3 | Dashboard | Anillo kcal, macros, alertas en tiempo real | ✅ |
| S4 | Registro texto | Texto libre + Open Food Facts API | ✅ |
| S5 | Registro foto | Claude Vision → estimación → confirmar | ✅ |
| S6 | Registro barcode | Open Food Facts por código de barras | ✅ |
| S7 | Progreso | Peso, medidas, fotos, gráficos tendencia | ✅ |
| S8 | Ejercicio | Catálogo, log, jerarquía +40, ajuste TDEE | ✅ |
| S9 | Planificación | Recetas IA, lista compras, presupuesto | ✅ |
| S10 | Meseta + periodización | Plateau, refeed, diet break automático | ✅ |
| S11 | Sueño/Cortisol | Registro sueño, alertas +40 | ✅ |
| S12 | Auth multi-usuario | Supabase Auth, login/registro | ✅ |
| S13 | i18n ES/EN | Selector idioma, todas las cadenas | ✅ |
| S14 | QA + Deploy | Tests, responsive, Streamlit Cloud | ✅ |

---

## CONTEXTO DEL DESARROLLADOR

- SO: Windows 10/11, AppLocker activo (solo .bat, sin .ps1/.vbs)
- IDE: VS Code + extensión Claude Code
- Repo: `socrates-cabral/ClaudeWork-` (branch `main`)
- Carpeta: `C:\ClaudeWork\HackeaMetabolismo\`
- Puerto: 8505 (no colisionar con finanzas_personales:8503, NutriMetab:8504)
- Python: `py` / `py -m pip`

## DEPENDENCIAS ESPECIALES
```
supabase==2.28.3   # instalar con --no-deps + deps manuales (pyiceberg conflict)
httpx[http2]       # requerido por supabase (h2 package)
```
Orden de instalación si hay problemas:
```
py -m pip install supabase --no-deps
py -m pip install postgrest gotrue storage3 realtime supabase_auth supabase_functions --no-deps
py -m pip install "storage3==0.8.1" --no-deps
py -m pip install deprecation
py -m pip install "httpx[http2]"
```

## ESTADO FINAL
- S1–S14: todos completos ✅
- Tests: 20/20 ✅
- Syntax check: 24/24 archivos ✅
- Supabase Auth: conectado y funcional ✅
- i18n: ES/EN con ~200 claves, selector en sidebar ✅
- UI dark theme: inputs/selectbox/calendar/tabs/botones en dark navy ✅
- Bugs post-QA resueltos: 5 fixes adicionales (ver historial abajo)

## BUGS RESUELTOS (historial)
| Archivo | Bug | Fix |
|---|---|---|
| `03_Registro.py:61` | f-string anidada con comillas escapadas | separado en variable `marca_txt` |
| `02_Dashboard.py:15` | `get_usuario` importado sin usar | eliminado del import |
| `03_Registro.py:136` | `prot_nueva` asignada sin usar | eliminada |
| `08_Meseta.py:75,107` | check idioma con `t("app.title").startswith(...)` frágil | reemplazado con `lang() == "es"` |
| `07_Sueno.py:65` | sin `st.rerun()` al guardar sueño | agregado `st.rerun()` |

## BUGS RESUELTOS — Precisión Nutricional (2026-03-31)
| Archivo | Bug | Fix |
|---|---|---|
| `vision_ia.py:PROMPT_VISION` | Valores numéricos en template JSON (32g prot, 28g carbs, 8g grasa) anclaban respuesta del AI | Reemplazados por placeholders descriptivos `<gramos reales>` |
| `vision_ia.py` | Sin validación de coherencia calórica — macros incoherentes pasaban sin detección | Agregada `_validar_coherencia()`: si kcal difieren >25% de prot×4+cho×4+grasa×9, recalcula |
| `recetas_ia.py:PROMPT_RECETAS` | Valores ejemplo anclados (450 kcal, 38g prot, 35g carbs, 12g grasa) | Reemplazados por `<calculados>` + regla explícita de coherencia |
| `03_Registro.py` Tab Manual | Defaults prerellenados (200/20/25/8) que usuario podía confirmar sin cambiar | Cambiados a `0.0` en los 4 campos |
| `openfoodfacts.py:_extraer_nutrientes` | `porcion_g` era string ("30g") inutilizable numéricamente | Nuevo `_parsear_porcion_g()` → float numérico; `porcion_str` conserva texto original |
| `03_Registro.py` Tab Barcode | Siempre 100g por defecto, sin considerar porción del envase | Pre-carga gramos con porción real del producto + banner informativo + vista previa ajustada |

## CONVENCIONES UI
- Dark theme: `#0a1628` (bg) · `#0d1f3c` (cards) · `#0f9d7a` (teal accent)
- CSS centralizado en `src/utils/styles.py` → `inject_styles()` en cada página
- Nunca usar CSS inline en páginas — todo va a `styles.py`
- Idioma: `lang()` de `src/utils/i18n.py` (no comparar strings de traducción)
